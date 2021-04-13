"""
Runs through all the current data in the Otter directory.
"""
from pathlib import Path
from argparse import ArgumentParser

from format_otter_data import editing

def edit_files(path, output_file):
    """
    Goes through all the files in a subdirectory and edits the .txt-files
    """
    # Go through all files.
    for full_path in path.iterdir():
        path_str = str(full_path)

        # Already edited files will be skipped.
        if "_edited.txt" in path_str: continue

        elif ".txt" in path_str:
            # Check what the output path should be. If the out
            output_file = str(output_file)
            if output_file == "same":
                output_file = path_str.replace(".txt", "_edited") + ".txt"
            editing(full_path, output_file)


def main(root_path, output_file):
    """
    The main function for running the data editing.
    """
    # Go through all the directories and check which of them that are directories.
    p = Path(root_path)
    for i in p.glob('**/*'):
        print(i)
        if i.is_dir():
            path = p / i.name
            edit_files(path, output_file)


if __name__ == "__main__":
    """
    Goes through all the files in the data directory and adds the edited files in the same directory. 
    --root_path: The path to the root-directory where all the data files are stored. 
    --output_path: The path where the data should be be stored. If it says "same", it is stored in the same directory as
                   the original file with the ending <filename>_edited.txt 
    """

    parser = ArgumentParser()
    parser.add_argument('--root_path', type=str, required=True)
    parser.add_argument('--output_file', type=str, required=True)
    args = parser.parse_args()
    main(args.root_path, args.output_file)

