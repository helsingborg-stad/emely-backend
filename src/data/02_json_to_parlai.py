"""
Transforms data from the .json format to a .txt-file that can be used when training Parlai.
"""
# !/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import random
from argparse import ArgumentParser
from pathlib import Path
import warnings


def get_first_data(job=None):
    """Returns the first data to each interaction as a string."""
    # TODO: Add better examples than just an empty string. For example have a list
    # TODO: of opening lines and sample from these.
    # TODO: format with position

    if job is None:
        input_list = ["Thanks for having me!", \
                      "I'm excited about this interview.", \
                      "I'm a little nervous but we can start the interview now.",
                      " "]
        i = random.randint(0, len(input_list) - 1)
        message = input_list[i]
    else:
        input_list = ["I'm applying for the job as __job__",
                      "I want to be a __job__",
                      "I'm here for the interview for the position as __job__"]
        i = random.randint(0, len(input_list) - 1)
        message = input_list[i].replace('__job__', job.lower().strip('\n'))
    return "text:{0}\t".format(message)


def open_json(path):
    """Opens the .json-files"""
    with open(path) as fp:
        data_str = json.load(fp)
    data = json.loads(data_str)
    return data


def extract_data(data, args):
    conv_length = data["len"]
    tags = {"u": "text", "e": "labels"}
    ending = {"u": "\t", "e": "\n"}

    #  Different ways of creating the beginning of the parlai formatted data
    if args.no_hardcoded_question:
        output = ''
    elif data['emely_start'] and args.add_position_context:
        output = get_first_data(job=data['position'])
    elif args.hardcoded_question_as_context and data['emely_start']:
        output = ''
    elif data['emely_start']:
        output = get_first_data()
    else:
        output = ''

    k = 1
    # Go through all the dialogue string.
    # Skip the first entry as this is one of the basic questions asked by Emely.
    for data_tup in data["dialog"]:
        if args.no_hardcoded_question and k == 1:
            k += 1
            continue
        elif args.hardcoded_question_as_context and data['emely_start']:
            # We want the first part of the episode to be: text:<emelys hardcoded question>\n<user reply>
            if k == 1:
                hardcoded_question = data_tup[1].strip('\n').strip()
                k += 1
                continue
            elif k == 2:
                question_reply = data_tup[1].strip('\n').strip()
                output = 'text:{}{}{}\t'.format(hardcoded_question, r'\n',
                                                question_reply)  # We format with a literal \n here. Important!
                k += 1  # We skip the two first iterations since we've done em here
                continue
            else:
                pass

        u_or_e = data_tup[0]
        text = data_tup[1].replace("\n", "")  # Remove the line break.
        text = text.strip()  # Trim whitespaces
        # Check if the interaction contains XXX(literally XXX). This is a placeholder for the text
        # and if it is contained in the text, the entire dialogue should be thrown out.
        if "XXX" in text:
            return "contained XXX", False

        tag = tags[u_or_e]
        end = ending[u_or_e]
        if k == conv_length:
            # Check if the last tag is a text or a label:
            if tag == "labels":
                output += "{0}:{1}\tepisode_done:True\n".format(tag, text)
            elif tag == "text":
                # Remove the last line break.

                warnings.warn("Last tag is text")
                output = output.rsplit('\n', 1)[0]  # Removes everything after the last tag
                output += "\tepisode_done:True\n"
        else:
            output += "{0}:{1}{2}".format(tag, text, end)
        k += 1
    return output, True


def main(input_path, output_filename, args):
    """ Main function that loops through all .json files in the desired directory.
        --input_path: The path to the .json-files
        --output_path: The path where the text-file is stored.
    """
    # Define the output file.
    output_string = ""
    data_dir = Path(__file__).resolve().parents[2].joinpath('data')
    out_path = data_dir / 'parlai'
    store_path = out_path.joinpath(output_filename)

    if not out_path.is_dir():
        out_path.mkdir(parents=True, exist_ok=True)

    # Go through all the .json files.
    for i in Path(data_dir / input_path).glob('**/*'):
        data = open_json(i)
        output, data_bool = extract_data(data, args)  # Get the correctly formated data
        # Check if the data should be appended.

        if not data_bool:
            warning_string = "The data:\n {0}\n  {1}. Not adding data.".format(data, output)
            warnings.warn(warning_string)
            continue
        else:
            output_string += output  # Append the output.data

    f = open(store_path, "w")
    f.write(output_string)
    f.close()


if __name__ == "__main__":
    """
    Goes through all the files in the data directory and adds the edited files in the same directory. 
    --input_path: The path to the input-directory where all the .json files are stored. 
    --output_filename: The path where the data should be be stored. 
    --no_hardcoded_question: Skips the first question in the dialogue
    --add_position_context: Adds something before emelys question
    --hardcoded_question_as_context: Formats the data similarly to blended_skill_talk where the the model gets two interactions as context
    """

    parser = ArgumentParser()
    parser.add_argument('--input_path', type=str, required=True, help='Relative to /data/')
    parser.add_argument('--output_filename', type=str, required=True, help='Relative to /data/parlai/')
    parser.add_argument('--no_hardcoded_question', action='store_true', required=False,
                        help='Skips hardcoded question in parlai data')
    parser.add_argument('--add_position_context', action='store_true', required=False)
    parser.add_argument('--hardcoded_question_as_context', action='store_true', required=False)
    parser.set_defaults(no_hardcoded_question=False,
                        add_position_context=False,
                        hardcoded_question_as_context=True)
    args = parser.parse_args()
    main(args.input_path, args.output_filename, args)
