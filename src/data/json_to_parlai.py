"""
Transforms data from the .json format to a .txt-file that can be used when training Parlai.
"""
import json
from argparse import ArgumentParser

from pathlib import Path

def open_json(path):
    """Opens the .json-files"""
    with open(path) as fp:
        data_str = json.load(fp)
    data = json.loads(data_str)
    return data

def extract_data(data):
    conv_length = data["len"]
    tags = {"u": "text", "e": "labels"}
    ending = {"u": "\t", "e": "\n"}
    output = ""

    k = 2
    # Go through all the dialouge string.
    # Skip the first entry as this is one of the basic questions asked by Emely.
    for data_tup in data["dialouge"][1:]:

        u_or_e = data_tup[0]
        text = data_tup[1].replace("\n", "")  # Remove the line break.
        tag = tags[u_or_e]
        end = ending[u_or_e]
        if k == conv_length:
            output += "{0}: {1} \t episode_done:True {2}".format(tag, text, end)
        else:
            output += "{0}: {1} {2}".format(tag, text, end)
        k += 1
    return output


def main(input_path, output_path):
    """ Main function that loops through all .json files in the desired directory.
        --input_path: The path to the .json-files
        --output_path: The path where the text-file is stored.
    """
    # Define the output file.
    output_string = ""
    data_dir = Path(__file__).resolve().parents[2]
    # Go through all the .json files.


    out_path = data_dir / output_path

    if not out_path.is_dir():
        out_path.mkdir(parents=True, exist_ok=True)

    store_path = str(out_path)

   # Go through all the .json files.
    for i in Path(data_dir / input_path).glob('**/*'):
        data = open_json(i)
        output = extract_data(data)  # Get the correctly formated data
        output_string += output  # Append the output.

    f = open(store_path + r"\\training_for_parlai.txt", "w")
    f.write(output_string)

if __name__ == "__main__":
    """
    Goes through all the files in the data directory and adds the edited files in the same directory. 
    --root_path: The path to the root-directory where all the .json files are stored. 
    --output_path: The path where the data should be be stored. If it says "same", it is stored in the same directory as
                   the original file with the ending <filename>_edited.txt 
    """

    parser = ArgumentParser()
    parser.add_argument('--root_path', type=str, required=True)
    parser.add_argument('--output_path', type=str, required=True)
    args = parser.parse_args()
    main(args.root_path, args.output_path)
