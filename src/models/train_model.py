from transformers import BlenderbotSmallForConditionalGeneration, BlenderbotSmallTokenizer, BlenderbotTokenizer, \
    BlenderbotForConditionalGeneration
from torch.utils.data import DataLoader, Dataset
import pandas as pd
from pathlib import Path
from src.models.model import LitBlenderbot, encode_sentences

import pytorch_lightning as pl
from pytorch_lightning.callbacks import ModelCheckpoint, EarlyStopping

from datetime import datetime
from argparse import ArgumentParser


# Dataloader tokenizer(batch, return_tensors='pt', padding=True, truncation=True, max_length=128)

class InterviewDataset(Dataset):
    def __init__(self, csv_path):
        self.dataframe = pd.read_csv(csv_path)

    def __len__(self):
        return len(self.dataframe)

    def __getitem__(self, item):
        return self.dataframe.iloc[item]['src'], self.dataframe.iloc[item]['target']


def token_collate_fn(batch):
    # Is it bad practice to access tokenizer from outer scope?
    batch = encode_sentences(tokenizer, batch)
    return batch


def load_model(mname):
    """Loads model from huggingface or locally. Works with both BlenderbotSmall and regular"""
    # TODO: Add loading from checkpoint
    model_dir = Path(__file__).resolve().parents[2] / 'models' / mname / 'model'
    token_dir = Path(__file__).resolve().parents[2] / 'models' / mname / 'tokenizer'
    assert model_dir.exists() and token_dir.exists()

    if 'small' in mname:
        model = BlenderbotSmallForConditionalGeneration.from_pretrained(model_dir)
        tokenizer = BlenderbotSmallTokenizer.from_pretrained(token_dir)
    else:
        model = BlenderbotForConditionalGeneration.from_pretrained(model_dir)
        tokenizer = BlenderbotTokenizer.from_pretrained(token_dir)
    return model, tokenizer


def main(hparams):
    now = datetime.now()
    global tokenizer  # Dirty fix for collate_fn
    model, tokenizer = load_model(mname=hparams.model_name)  # TODO: Add option to start from checkpoint!
    lightning_model = LitBlenderbot(model=model, tokenizer=tokenizer, hparams=hparams)

    project_dir = Path(__file__).resolve().parents[2]
    train_path = project_dir / 'data' / hparams.train_set
    val_path = project_dir / 'data' / hparams.val_set
    checkpoint_path = project_dir / 'models' / '{}@{}'.format(hparams.model_name, now.strftime("%Y_%m_%d_%H_%M"))
    checkpoint_path.mkdir(parents=True, exist_ok=True)

    train_set = InterviewDataset(train_path)
    val_set = InterviewDataset(val_path)

    # TODO: Fix hparams with hydra!
    train_loader = DataLoader(train_set, collate_fn=token_collate_fn, batch_size=hparams.batch_size)
    val_loader = DataLoader(val_set, collate_fn=token_collate_fn, batch_size=hparams.batch_size)

    ## Checkpoint callbacks
    checkpoint_callback = ModelCheckpoint(
        dirpath=checkpoint_path,
        save_top_k=1,
        verbose=True,
        monitor='val_loss',
        mode='min'
    )

    ## Ealy stopping callback
    early_stopping = EarlyStopping(
        monitor='val_loss',
        min_delta=0.00,
        patience=5,
        verbose=False,
        mode='min'
    )

    params = {'gpus': 1,
              'auto_scale_batch_size': False
              }
    trainer = pl.Trainer(**params,
                         callbacks=[checkpoint_callback, early_stopping],
                         default_root_dir=checkpoint_path)
    trainer.fit(lightning_model, train_loader, val_loader)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--model_name', type=str, required=True,
                        help='pretrained model to start from. will look for model in models/')
    parser.add_argument('--learning_rate', type=int, default=5e-6)
    parser.add_argument('--batch_size', type=int, default=4)
    parser.add_argument('--train_set', type=str, required=True, help='path to train set csv relative to data/')
    parser.add_argument('--val_set', type=str, default='processed/interview_val.csv',
                        help='path to train set csv relative to data/')
    parser.add_argument('--acc_gradients', type=int, default=3)
    hparams = parser.parse_args()

    main(hparams)
