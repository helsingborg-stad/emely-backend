from transformers import BlenderbotTokenizer, BlenderbotForConditionalGeneration, BlenderbotSmallTokenizer, \
    BlenderbotSmallForConditionalGeneration

from pathlib import Path

if __name__ == '__main__':
    mname = 'facebook/blenderbot-400M-distill'
    model_name = mname.replace('facebook/', '')
    model = BlenderbotForConditionalGeneration.from_pretrained(mname)
    tokenizer = BlenderbotTokenizer.from_pretrained(mname)

    model_dir = Path.cwd().joinpath(model_name + '/model')
    token_dir = Path.cwd().joinpath(model_name + '/tokenizer')

    model_dir.mkdir(parents=True, exist_ok=True)
    token_dir.mkdir(parents=True, exist_ok=True)

    model.save_pretrained(model_dir)
    tokenizer.save_pretrained(token_dir)
