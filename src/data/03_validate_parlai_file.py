from pathlib import Path
from argparse import ArgumentParser
import warnings
import re

""" This script checks a txt file and validates that it's in the correct parlai format, e.g:

    text:Hello my name is Earl\tlabels:That's not true!\n
    text:You got me, I lied\tlabels:Shame on you.\tepisode_done:True\n
    ...
    and so on
"""


def validate(file):
    file_path = Path(__file__).resolve().parents[2] / 'data/parlai' / file
    print('looking for file ', file_path.as_posix())
    assert file_path.exists(), "Couldn't find file {}".format(file_path)

    with open(file_path, 'r') as f:
        text = f.read()

    # Split on \tepisode_done:True\n
    # This should yield strings with alternating 'text:<text>\tlabel:<text>\n' which we can check for.
    # And nowhere should episode_done be found!!
    episodes = text.split('\tepisode_done:True\n')

    for episode in episodes:

        # Test for wrongly formatted episode_done
        if 'episode_done' in episode:
            warnings.warn('Found episode done in episode:')
            print(episode)

        # Split on tab and newline to get list of text and labels alternating
        messages = re.split(r'[\n\t]', episode)
        messages = list(filter(None, messages))  # FIlter out potential empty strings
        if len(messages) == 0:
            if episode == episodes[-1]:  # Last one will be empty
                continue
            else:
                warnings.warn('Found empty episode')
                print(episode)
                continue

        if 'text:' not in messages[0]:
            warnings.warn('Did not find text: in the beginning of the episode')

        for i, message in enumerate(messages):
            tokens = ['text:', 'labels:']
            index = i % 2
            expected_token = tokens.pop(index)
            unexpected_token = tokens.pop()
            if expected_token not in message:
                warnings.warn("Didn't find the expected token in the message")
                print('Expected token was {}'.format(expected_token))
                print('Message was: {}'.format(message))
            if unexpected_token in message:
                warnings.warn("Found unexpected token in the message")
                print('Unexpected token was {}'.format(unexpected_token))
                print('Message was: {}'.format(message))

    print("If there were no other messages you're all good :) ")


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-i', '--input_file', type=str, required=True)
    args = parser.parse_args()
    validate(args.input_file)
