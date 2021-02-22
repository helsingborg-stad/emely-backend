from transformers import BlenderbotForConditionalGeneration, BlenderbotTokenizer
from torch.utils.data import DataLoader, TensorDataset, random_split, RandomSampler, Dataset
import pandas as pd
import numpy as np
from pathlib import Path

import torch.nn.functional as F
import pytorch_lightning as pl
import torch
from pytorch_lightning.callbacks import ModelCheckpoint

class LitBlenderbot(pl.LightningModule):
    def __init__(self, tokenizer, model, hparams):
        super().__init__()
        self.tokenizer = tokenizer
        self.model = model
        self.hparams = hparams

        self.freeze_model_parts()

    def freeze_model_parts(self):
        # TODO: Add option define what is frozen here?
        freeze_params(self.model)
        unfreeze_params(self.model.lm_head)
        return

    def forward(self, x):
        # String to string since it's inference?
        inputs = self.tokenizer([x], return_tensors='pt')
        output_tokens = self.model.generate(**inputs)
        reply = self.tokenizer.decode(output_tokens[0], skip_special_tokens=True)
        return reply

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=self.hparams.learning_rate)
        return optimizer

    def training_step(self, train_batch, batch_idx):
        x, y = train_batch

        output = self(input_ids=x['input_ids'],
                      attention_mask=x['attention:mask'],
                      decoder_input_ids=y['input_ids'],
                      decoder_attention_mask=y['attention:mask'],
                      use_cache=False)
        self.log('train_loss', output.loss)
        return output.loss

    def validation_step(self, val_batch, batch_idx):
        loss = 0
        self.log('val_loss', loss)
        return loss



def freeze_params(model):
  """ Freezes all parameters in a model"""
  for layer in model.parameters():
    layer.requires_grad = False

def unfreeze_params(model):
    """ Unfreezes all parameters in a model"""
    for layer in model.parameters():
        layer.requires_grad = True


def encode_sentences(tokenizer, source_sentences, target_sentences, max_length=127, pad_to_max_length=None):
    ''' Function that tokenizes a sentence
        Args: tokenizer - the Blenderbot tokenizer; source and target sentences are the source and target sentences
        Returns: Dictionary with keys: input_ids, attention_mask, target_ids
    '''

    input_ids = []
    attention_masks = []
    target_ids = []
    tokenized_sentences = {}

    for sentence in source_sentences:
        encoded_dict = tokenizer(
            sentence,
            max_length=max_length,
            padding="max_length" if pad_to_max_length else None,
            truncation=True,
            return_tensors='pt'
        )
        input_ids.append(encoded_dict['input_ids'])
        attention_masks.append(encoded_dict['attention_mask'])

    input_ids = torch.cat(input_ids, dim=0)
    attention_masks = torch.cat(attention_masks, dim=0)

    for sentence in target_sentences:
        encoded_dict = tokenizer(
            sentence,
            max_length=max_length,
            padding="max_length" if pad_to_max_length else None,
            truncation=True,
            return_tensors='pt'
        )
        # Shift the target ids to the right
        # shifted_target_ids = shift_tokens_right(encoded_dict['input_ids'], tokenizer.pad_token_id)
        target_ids.append(encoded_dict['input_ids'])

    target_ids = torch.cat(target_ids, dim=0)

    batch = {
        "input_ids": input_ids,
        "attention_mask": attention_masks,
        "labels": target_ids,
    }

    return batch

def shift_tokens_right(input_ids, pad_token_id):
  """ Shift input ids one token to the right, and wrap the last non pad token (usually <eos>).
      This is taken directly from modeling_bart.py
  """
  prev_output_tokens = input_ids.clone()
  index_of_eos = (input_ids.ne(pad_token_id).sum(dim=1) - 1).unsqueeze(-1)
  prev_output_tokens[:, 0] = input_ids.gather(1, index_of_eos).squeeze()
  prev_output_tokens[:, 1:] = input_ids[:, :-1]
  return prev_output_tokens
