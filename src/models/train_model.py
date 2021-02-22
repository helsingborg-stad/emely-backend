from transformers import BlenderbotForConditionalGeneration, BlenderbotTokenizer
from torch.utils.data import DataLoader, TensorDataset, random_split, RandomSampler, Dataset
import pandas as pd
import numpy as np
from pathlib import Path

import torch.nn.functional as F
import pytorch_lightning as pl
import torch
from pytorch_lightning.callbacks import ModelCheckpoint

import math
import random
import re
import argparse

# Dataloader tokenizer(batch, return_tensors='pt', padding=True, truncation=True, max_length=128)

class InterviewDataset(Dataset):
    def __init__(self, csv_path):
        self.dataframe = pd.read_csv(csv_path)

    def __len__(self):
        return len(self.dataframe)

    def __getitem__(self, item):
        return self.dataframe.iloc[item]['src'], self.dataframe[item]['target']


def token_collate_fn(batch):
    # Is it bad practice to access tokenizer from outer scope?
    src_list, target_list = [], []
    for _src, _target in batch:
        src_list.append(_src)
        target_list.append(_target)
    x = tokenizer(src_list, return_tensors='pt', padding=True, truncation=True, max_length=128)
    y = tokenizer(target_list, return_tensors='pt', padding=True, truncation=True, max_length=128)
    return x, y  # If you end up here, the model probably can't handle x and y of different lengths


if __name__ == '__main__':

    # TODO: Add option to start from checkpoint!
    mname = 'facebook/blenderbot-400M-distill'  # TODO: Add this as click
    tokenizer = BlenderbotTokenizer.from_pretrained(mname)
    model = BlenderbotForConditionalGeneration.from_pretrained(mname)
    hparams = None
    lightning_model = LitBlenderbot(model=model, tokenizer=tokenizer, hparams=hparams)

    project_dir = Path(__file__).resolve().parents[2]
    train_path = project_dir.joinpath('data/processed/interview_train.csv')
    val_path = project_dir.joinpath('data/processed/interview_val.csv')

    train_set = InterviewDataset(train_path)
    val_set = InterviewDataset(val_path)
    train_loader = DataLoader(train_set, collate_fn=token_collate_fn)
    val_loader = DataLoader(val_set, collate_fn=token_collate_fn)

    # TODO: Saving the model checkpoints!
    trainer = pl.Trainer(gpus=1)
    trainer.fit(lightning_model, train_loader, val_loader)
