from transformers import BlenderbotForConditionalGeneration, BlenderbotTokenizer
from torch.utils.data import DataLoader, TensorDataset, random_split, RandomSampler, Dataset
import pandas as pd
from pathlib import Path
from src.models.model import LitBlenderbot, encode_sentences

import pytorch_lightning as pl
import torch
from pytorch_lightning.callbacks import ModelCheckpoint

import math
import random
import re
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

def main(hparams):
    # TODO: Add option to start from checkpoint!
    mname = 'facebook/blenderbot-400M-distill'  # TODO: Add this as click
    global tokenizer # Dirty fix for collate_fn
    tokenizer = BlenderbotTokenizer.from_pretrained(mname)
    model = BlenderbotForConditionalGeneration.from_pretrained(mname)
    lightning_model = LitBlenderbot(model=model, tokenizer=tokenizer, hparams=hparams)

    train_path = project_dir.joinpath('data/processed/interview_train.csv')
    val_path = project_dir.joinpath('data/processed/interview_val.csv')

    train_set = InterviewDataset(train_path)
    val_set = InterviewDataset(val_path)

    # TODO: Fix hparams with hydra!
    train_loader = DataLoader(train_set, collate_fn=token_collate_fn, batch_size=hparams.batch_size)
    val_loader = DataLoader(val_set, collate_fn=token_collate_fn, batch_size=hparams.batch_size)

    # TODO: Saving the model checkpoints!
    trainer = pl.Trainer.from_argparse_args(hparams)
    trainer.fit(lightning_model, train_loader, val_loader)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--learning_rate', type=int, default=0.001)
    parser.add_argument('--gpus', type=int, default=1)
    parser.add_argument('--batch_size', type=int, default=4)
    parser.add_argument('--auto_scale_batch_size', type=str, default='power')
    hparams = parser.parse_args()

    project_dir = Path(__file__).resolve().parents[2]

    main(hparams)

