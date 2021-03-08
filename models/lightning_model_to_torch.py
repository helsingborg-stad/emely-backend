from src.models.model import LitBlenderbot
from pathlib import Path
from transformers import BlenderbotTokenizer, BlenderbotSmallTokenizer
from argparse import Namespace

if __name__ == '__main__':
    """" Loads a lightning checkpoint and saves tokenizer and model as bin in same directory"""
    # Model run and checkpoint name
    model_run = 'blenderbot_small-90M@2021_03_08_13_49'
    checkpoint = 'epoch=699-step=25199.ckpt'

    ###################### Start of script ##########################

    cwd = Path(__file__).resolve().parent
    model_dir = cwd / model_run
    checkpoint_dir = model_dir / checkpoint

    if 'small' in model_run:
        mname = 'blenderbot_small-90M'
        tokenizer_dir = cwd / mname / 'tokenizer'
        tokenizer = BlenderbotSmallTokenizer.from_pretrained(tokenizer_dir)
    else:
        mname = model_run.split('@')[0]
        tokenizer_dir = cwd / mname / 'tokenizer'
        tokenizer = BlenderbotTokenizer.from_pretrained(tokenizer_dir)

    kwargs = {'mname': mname, 'tokenizer': tokenizer, 'hparams': Namespace()}
    litmodel = LitBlenderbot.load_from_checkpoint(checkpoint_path=checkpoint_dir, **kwargs)
    litmodel.model.save_pretrained(model_dir / 'model')
    litmodel.tokenizer.save_pretrained(model_dir / 'tokenizer')
