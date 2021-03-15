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


def load_tokenizer(mname):
    """Loads model locally. Works with both BlenderbotSmall and regular"""
    token_dir = Path(__file__).resolve().parents[2] / 'models' / mname / 'tokenizer'
    assert token_dir.exists()

    if 'small' in mname:
        tokenizer = BlenderbotSmallTokenizer.from_pretrained(token_dir)
    else:
        tokenizer = BlenderbotTokenizer.from_pretrained(token_dir)
    return tokenizer


def main(hparams):
    now = datetime.now()
    global tokenizer  # Dirty fix for collate_fn
    tokenizer = load_tokenizer(mname=hparams.model_name)
    lightning_model = LitBlenderbot(mname=hparams.model_name, tokenizer=tokenizer, hparams=hparams)

    # Paths
    project_dir = Path(__file__).resolve().parents[2]
    train_path = project_dir / 'data' / hparams.train_set
    val_path = project_dir / 'data' / hparams.val_set
    model_type = hparams.model_name.strip('blenderbot_')
    checkpoint_path = project_dir / 'models' / '{}@{}'.format(hparams.model_name, now.strftime("%d_%H_%M"))
    checkpoint_path.mkdir(parents=True, exist_ok=True)

    if hparams.resume_from_checkpoint is not None:
        if 'ckpt' in hparams.resume_from_checkpoint:
            old_checkpoint = project_dir / 'models' / hparams.resume_from_checkpoint
            assert old_checkpoint.exists(), "checkpoint directory doesn't exist"
        else:  # we only specify the dir so we take the latest
            checkpoint_dir = project_dir / 'models' / hparams.resume_from_checkpoint
            checkpoints = [file.name for file in checkpoint_dir.iterdir() if file.is_file()]
            checkpoints = sorted(checkpoints, key=lambda x: x[6:9])
            old_checkpoint = checkpoints[-1]
    else:
        old_checkpoint = None

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

    ## Early stopping callback
    early_stopping = EarlyStopping(
        monitor='val_loss',
        min_delta=0.00,
        patience=5,
        verbose=False,
        mode='min'
    )

    trainer = pl.Trainer(gpus=hparams.gpus,
                         auto_scale_batch_size=hparams.auto_scale_batch_size,
                         callbacks=[checkpoint_callback, early_stopping],
                         default_root_dir=checkpoint_path,
                         resume_from_checkpoint=old_checkpoint)
    trainer.fit(lightning_model, train_loader, val_loader)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--model_name', type=str, required=True,
                        help='pretrained model to start from. will look for model in models/')
    parser.add_argument('--train_set', type=str, required=True, help='path to train set csv relative to data/')

    parser.add_argument('--learning_rate', type=float, default=5e-6)
    parser.add_argument('--batch_size', type=int, default=4)
    parser.add_argument('--gpus', type=int, default=1)
    parser.add_argument('--val_set', type=str, default='processed/interview_val.csv',
                        help='path to train set csv relative to data/')
    parser.add_argument('--acc_gradients', type=int, default=1)
    parser.add_argument('--auto_scale_batch_size', action='store_true', default=False)
    parser.add_argument('--resume_from_checkpoint', type=str, default=None,
                        help='Dir under /models/ to resume from')
    parser.add_argument('--auto_lr_find', action='store_true', default=False)
    parser.add_argument('--check_val_every_n_epoch ', type=int, default=1)
    parser.add_argument('--max_epochs', type=int, default=20)

    hparams = parser.parse_args()

    main(hparams)
