import json
from src.chat.translate import ChatTranslator  # Use the Emely translate API. This requries the correct .json key file.
from argparse import ArgumentParser
from pathlib import Path
from typing import Dict


translator = ChatTranslator()


def open_json(path: Path) -> Dict:
    """Opens the .json-files"""

    with open(path) as fp:
        data_str = json.load(fp)
    data = json.loads(data_str)

    return data

def save_json(conversation: Dict, save_path: Path):
    """Saves .json"""

    json_str = json.dumps(conversation)
    with open(save_path, 'w') as f:
        json.dump(json_str, f)
    
    return



def translate_json_dialog(conversation: Dict) -> Dict:
    """ Translates the dialog from swedish to english and returns a new json with the translated dialog """
    dialog = conversation['dialog']

    # Goes through each turn in the conversation and replaces the text with the translation
    for turn in dialog:
        text = turn[1]
        turn[1] = translator.translate(text, src= 'sv', target='en')

    return conversation


def main(input_path, output_path):

    data_dir = Path(__file__).resolve().parents[2].joinpath('data')
    json_path = data_dir / input_path
    translated_json_path = data_dir / output_path

    translated_json_path.mkdir(parents=True, exist_ok=True)
    assert json_path.exists

    for file in json_path.iterdir():
        if file.suffix == '.json':
            save_path = translated_json_path / file.name
            conversation = open_json(file)
            translated_conversation = translate_json_dialog(conversation)
            save_json(translated_conversation, save_path)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--input_path', type=str, required=True, help='Relative to /data/')
    parser.add_argument('--output_path', type=str, required=True, help='Relative to /data/')

    args = parser.parse_args()
    main(args.input_path, args.output_path)
