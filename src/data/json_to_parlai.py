"""
Transforms data from the .json format to a .txt-file that can be used when training Parlai.
"""
import json
import random
from argparse import ArgumentParser
from pathlib import Path


def get_first_data(position):
    """Returns the first data to each interaction as a string."""
    # TODO: Add better examples than just an empty string. For example have a list
    # TODO: of opening lines and sample from these.
    # TODO: Posibly format with position here! Check if it is empty or not though

    input_list = ["Thanks for having me!", \
                  "I'm excited about this interview.", \
                  "I'm a little nervous but we can start the interview now.",
                  " "]
    i = random.randint(0, len(input_list) - 1)
    return "text:{0}\t".format(input_list[i])  # Begin each new dialouge with an empty string as input.


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

    if data['emely_start']:
        output = get_first_data(data['position'])
    else:
        output = ''

    k = 1
    # Go through all the dialouge string.
    # Skip the first entry as this is one of the basic questions asked by Emely.
    for data_tup in data["dialouge"]:

        u_or_e = data_tup[0]
        text = data_tup[1].replace("\n", "")  # Remove the line break.
        text = text.strip()  # Trim whitespaces
        # Check if the interaction contains XXX. This is a placeholder for the text
        # and if it is contained in the text, the entire dialouge should be thrown out.
        if "XXX" in text:
            return "", False

        tag = tags[u_or_e]
        end = ending[u_or_e]
        if k == conv_length:
            # Check if the last tag is a text or a label:
            if tag == "labels":
                output += "{0}:{1}\tepisode_done:True\n".format(tag, text)
            elif tag == "text":
                # Remove the last line break.
                # TODO: This is a hotfix for when the last input is a text and not a label.
                output = output[:-1]
                output += "episode_done:True\n"
        else:
            output += "{0}:{1}{2}".format(tag, text, end)
        k += 1
    return output, True


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
        output, data_bool = extract_data(data)  # Get the correctly formatted data
        # Check if the data should be appended.
        if not data_bool:
            Warning("The data:\n {0}\n  contained XXX. Not adding data.".format(data))
        output_string += output  # Append the output.

    f = open(store_path + r"\\training_for_parlai.txt", "w")
    f.write(output_string)


if __name__ == "__main__":
    """
    Goes through all the files in the data directory and adds the edited files in the same directory. 
    --input_path: The path to the input-directory where all the .json files are stored. 
    --output_path: The path where the data should be be stored. If it says "same", it is stored in the same directory as
                   the original file with the ending <filename>_edited.txt 
    """

    parser = ArgumentParser()
    parser.add_argument('--input_path', type=str, required=True)
    parser.add_argument('--output_path', type=str, required=True)
    args = parser.parse_args()
    main(args.input_path, args.output_path)
