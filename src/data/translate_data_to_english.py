"""
Script for preprocessing the dialouge data where there are multiple interactions between Emely and the user.

"""
#!/usr/bin/env python
# -*- coding: utf-8 -*-






from pathlib import Path
from argparse import ArgumentParser
from src.data.utils import store_as_txt, open_with_errors
from src.chat.translate import ChatTranslator  # Use the Emely translate API. This requries the correct .json key file.

translator = ChatTranslator()


def find_tag(line):
    """Find the tag of a line consisting of emely, user of position"""
    if "user:" in line:
        return "user:"
    elif "emely:" in line:
        return "emely:"
    elif "Position:" in line:
        return "position:"
    elif "position:" in line:
        return "position:"
    else:
        return ""


def run_data_translation(lines, output_path, file_name):
    """Goes through all lines and translates each line containing Emely or User to english.
       --lines: The the text lines.
       --output_path: The path where the data are stored.
       --file_name: The original file name.
    """

    output = ""

    # TODO: Fix so that the functions checks that episode_done and episode_start alternates.
    for k, line in enumerate(lines):
        # Test if there there is a new position
        tag = find_tag(line)
        # Test if the tag is something else than an empty string.
        if tag !="":

            line_tmp = line.split(tag)[1]
            translate_text = translator.translate(line_tmp, src="sv", target="en")
            new_line = "{0} {1}\n".format(tag, translate_text)

            output += new_line
        else:
            output += line
    # Create the store_name and the entire store_path.

    store_name = file_name.replace(".txt", "_en.txt")
    store_path = str(output_path) + store_name

    store_as_txt(output, store_path)





def main(input_path, store_path):
    """
    Goes through all files in the input path and turns the dialoges to .json files.
    """

    # The path for the raw data must be here.
    data_dir = Path(__file__).resolve().parents[2].joinpath('data')
    input_path = data_dir / input_path
    output_path = data_dir / store_path

    # Check if the output path exists. If not make it.
    output_path = Path(output_path)
    if not output_path.is_dir():
        output_path.mkdir(parents=True, exist_ok=True)

    # Go through all files in the input_path.
    paths = input_path.glob('**/*')
    for i in paths:
        # Read the lines.
        current_file_name = str(i).split(str(input_path))[1]

        try:
            # Some files
            with open(i) as fp:
                lines = fp.readlines()
        except:
            print("Could not open file {0} using the normal format. Using the codecs package to open data.".format(i))

            lines = open_with_errors(i)
        run_data_translation(lines, output_path, current_file_name)


if __name__ == "__main__":
    """
    To call the function from the terminal supply two input arguments.
    --input_path: The path to the input file(s).
    --output_path: The name of the subdirectory where the translated txt-file will be stored. The filename will be
                   <file_name>_en.txt.
                    
    """
    parser = ArgumentParser()
    parser.add_argument('--input_path', type=str, required=True)
    parser.add_argument('--output_path', type=str, required=True)
    args = parser.parse_args()

    main(args.input_path, args.output_path)




