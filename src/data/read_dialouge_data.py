"""
Script for preprocessing the dialouge data where there are multiple interactions between Emely and the user.

"""

import secrets
import json

from pathlib import Path
from argparse import ArgumentParser
import warnings
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


    if "emely:" in line or "Emely:" in line:
        output = ("e", line.replace("emely:", ""))
    elif "user:" in line or "User: " in line:
        output = ("u", line.replace("user:", ""))
    elif line == "\n":
        # If there is a line break, remove it.
        return False
    else:

        # Raise a warning if there is something wrong with the format.
        #
        return "raise_warning"
    return output

def check_emely_first(dialouge):
    """Checks so that the first entry is from Emely.
    --dialouge: A dialouge obejct
    """

    tag = dialouge.dialouge[0][0]
    if tag == "e":
        return True
    elif tag == "u":
        return False
    else:
        raise ValueError("The tag {0} is not in the correct format.".format(tag))

def store_data(dialouge, output_path):
    """Saves the data in the desried file"""

    # Check so that the first response is from Emely.
    if not check_emely_first(dialouge):
        # If it is not in the correct format, the data will not be stored.
        return False

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
    return True

def run_data_extraction(lines, output_path, file_path):
    """Goes through all lines and stores each interaction to a .json-file"""
    current_lines = []

    append_lines = False
    current_position = None  # The current job position.

    last_episode = "done"  # This is used to check what the last episode was.

    # TODO: Fix so that the functions checks that episode_done and episode_start alternates.
    for k, line in enumerate(lines):

        # Test if there there is a new position

        if "position: " in line:
            current_position = line.replace("position: ", "")

        # Check if the episode is finnished.
        if "episode_done" in line:
            # If the episode is done add the data
            # Initialise the Dialouge
            if not last_episode == "start":
                warnings.warn("There is not alternation between episode_start and episode_done. \n File {0} at line {1} "
                              "is excluded from analysis.".format(file_path, k))
                append_lines = False
                continue


            if current_lines[0][0] == "e": emely_start = True
            else: emely_start = False
            # Create the dialouge object.
            dialouge = Dialogue(len=len(current_lines),
                                position=current_position,
                                dialouge=current_lines,
                                emely_start=emely_start)
            # Store the data.
            store_bool = store_data(dialouge, output_path)
            # If the data storing is not correct, print the incorrect file
            if not store_bool:
                warning_msg = "The file {0} \n is incorrectly formatted at line {1}. \n Data is excluded from analysis.".format(file_path, k)
                warnings.warn(warning_msg)
            # Reset the current lines.
            current_lines = []
            # Reset the append lines.
            append_lines = False
            last_episode = "done"

        # Append the current line
        if append_lines:
            # transform the line to the correct format.
            line_f = format_line(line)

            if line_f =="raise_warning":
                print("Warning detected at in file \n{0} \n at line {1}.".format(file_path, k))
            elif line_f:
                current_lines.append(line_f)

        # Check if there is an episode start so that data should be appended.
        if "episode_start" in line:
            if last_episode != "done":
                warnings.warn(
                    "There is not alternation between episode_start and episode_done. \n File {0} at line {1} "
                    "is excluded from analysis.".format(file_path, k))
                continue
            last_episode = "start"
            append_lines = True


def remove_json(path: Path):
    """ Removes all .json files in the Path path. This is used in order to not create dubplicates"""

    for p in path.glob('**/*'):
        if ".json" in str(p):
            p.unlink()
            print("Removed file: {0}".format(str(p)))


def main(input_path, store_path, run_remove=False):
    """
    Goes through all files in the input path and turns the dialoges to .json files.
    """

    # The path for the rawdata must be here.
    data_dir = Path(__file__).resolve().parents[2]# .joinpath('data')
    input_path = data_dir / input_path# Path(input_path)
    output_path = data_dir / store_path

    # Check if the output path exists. If not make it.
    output_path = Path(output_path)
    if not output_path.is_dir():
        output_path.mkdir(parents=True, exist_ok=True)

    # Check if existing data should be removed.
    if run_remove:
        remove_json(output_path)
    # Remove all .json-files if there are any in the output path.

    # Go through all files in the input_path.
    for i in input_path.glob('**/*'):
        # Read the lines.

        with open(i) as fp:

            lines = fp.readlines()

        run_data_extraction(lines, output_path, i)


if __name__ == "__main__":
    # To call the function from the terminal supply two input arguments.
    # --input_path: The path to the input file(s).
    # --output_path: The name of the subdirectory where the .json-files should be stored. The file-names are randomly generated.
    #                If this path does not exist, it will be created. The default name should be json
    # --run_remove: Boolean. If true, it removes all files with the .json ending in the output path.

    parser = ArgumentParser()
    parser.add_argument('--input_path', type=str, required=True)
    parser.add_argument('--output_path', type=str, required=True)
    parser.add_argument("--run_remove", dest='run_remove', action='store_true')
    parser.set_defaults(run_remove=False)
    args = parser.parse_args()
    if args.run_remove:
        main(args.input_path, args.output_path, args.run_remove)
    else:
        main(args.input_path, args.output_path)


