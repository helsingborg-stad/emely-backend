"""
Script for preprocessing the dialouge data where there are multiple interactions between Emely and the user.

The files are stored
"""

import secrets
import json

from pathlib import Path
from argparse import ArgumentParser

from pydantic import BaseModel
from typing import Union


class Dialogue(BaseModel):
    # Dialouge class used to store each interaction.
    len: int  # The number of interactions between Emely and the User.
    emely_start: bool  # Determines if Emely starts of not.
    dialouge: list  # [str]
    position: Union[None, str]  #If there is a job position, this should be entered as a string, otherwise enter None.


def format_line(line: str):
    """Formats the line into a tuple """


    if "emely" in line:
        output = ("e", line.replace("emely:", ""))
    elif "user" in line:
        output = ("u", line.replace("user:", ""))
    else:
        #
        raise ValueError("Line is not in the correct format.: {0}. Make sure that the input file"
                         "is formatted according to the instructions".format(line))
    return output


def store_data(dialouge, output_path):
    """Saves the data in the desried file"""

    # Generate a random name.
    name = str(secrets.token_hex(nbytes=4)) + ".json"
    # Create the savepath
    save_path = Path(output_path).joinpath(name)
    # print(save_path)
    # Convert the dialouge object to a dict.
    json_str = json.dumps(dialouge.__dict__)

    # Store the .json-file. In order to access the data, the stored file must be open with json.load, which
    # is a string. In order to access the dict, the json.loads() must be used on the string.
    # Ex: file_string = json.load(filen_name), data = json.loads(file_string)

    with open(save_path.as_posix(), "w") as fp:
        json.dump(json_str, fp)


def run_data_extraction(lines, output_path):
    """Goes through all lines and stores each interaction to a .json-file"""
    current_lines = []

    append_lines = False
    current_position = None  # The current job position.

    for k, line in enumerate(lines):
        # Test if there there is a new position

        if "position: " in line:
            current_position = line.replace("position: ", "")

        # Check if the episode is finnished.
        if "episode_done" in line:
            # If the episode is done add the data
            # Initialise the Dialouge

            if current_lines[0][0] == "e":
                emely_start = True
            else:
                emely_start = False
            # Create the dialouge object.
            dialouge = Dialogue(len=len(current_lines),
                                position=current_position,
                                dialouge=current_lines,
                                emely_start=emely_start)
            #Store the data.
            store_data(dialouge, output_path)
            # Reset the current lines.
            current_lines = []
            # Reset the append lines.
            append_lines = False

        # Append the current line
        if append_lines:
            # transform the line to the correct format.
            line_f = format_line(line)
            current_lines.append(line_f)

        # Check if there is an episode start so that data should be appended.
        if "episode_start" in line:
            append_lines = True

def main(input_file, store_path):

    # The path for the rawdata must be here.
    data_dir = Path(__file__).resolve().parents[2].joinpath('data')
    input_path = data_dir / 'raw' / Path(input_file)
    output_path = data_dir / store_path

    # Check if the output path exists.
    print(input_path)
    print(data_dir)
    print(store_path)
    print(output_path)
    if not Path(output_path).is_dir():
        Path(output_path).mkdir(parents=True, exist_ok=True)

    # Read the lines.
    with open(input_path) as fp:
        lines = fp.readlines()
    # Check if the output path exist.

    # If not, create the path.
    run_data_extraction(lines, output_path)


if __name__ == "__main__":
    # To call the function from the terminal supply two input arguments.
    # --input_file: The filename to the input file. It is assumed that this is located in root/data/raw/.
    # --output_file: The name of the subdirectory where the .json-files should be stored. The file-names are randomly generated.
    #                If this path does not exist, it will be created. The default name should be json
    parser = ArgumentParser()
    parser.add_argument('--input_file', type=str, required=True)
    parser.add_argument('--output_file', type=str, required=True)
    args = parser.parse_args()
    main(args.input_file, args.output_file)

