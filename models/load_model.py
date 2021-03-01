from transformers import BlenderbotTokenizer, BlenderbotForConditionalGeneration
from pathlib import Path

if __name__ == '__main__':
    model_name = 'blenderbot-400M-distill'

    model_dir = Path.cwd().joinpath(model_name + '/model')
    token_dir = Path.cwd().joinpath(model_name + '/tokenizer')

    model = BlenderbotForConditionalGeneration.from_pretrained(model_dir)
    tokenizer = BlenderbotTokenizer.from_pretrained(token_dir)
