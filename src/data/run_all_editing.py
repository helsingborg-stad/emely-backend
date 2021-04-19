"""
Runs through all the current data in the Otter directory.
"""
from pathlib import Path
from argparse import ArgumentParser

from format_otter_data import editing

def edit_files(path, filename, output_path):
    """
    Goes through all the files in a subdirectory and edits the .txt-files
    """
    # Go through all files.
    #for full_path in path.():
    path_str = str(path)

    # Already edited files will be skipped.
    if "_edited.txt" in filename: return

    elif ".txt" in filename:

        # Check what the output path should be. If the out

        fn = filename.replace(".txt", "_edited") + ".txt"

        editing(str(path_str) + str(filename), fn, output_path)


def main(input_path, output_path):
    """
    The main function for running the data editing.
    """
    # Go through all the directories and check which of them that are directories.
    data_dir = Path(__file__).resolve().parents[2]#.joinpath('data')
    path = data_dir / Path(input_path)
    store_path = data_dir / Path(output_path)

    # 
    for filename in path.glob('**/*'):

        if ".txt" in str(filename):
            # Remove everything that is not the file_name
            filename = str(filename).replace(str(path), "")
            print("Filename: {0}".format(filename))

            edit_files(path, filename, store_path)


if __name__ == "__main__":
    """
    Goes through all the files in the data directory and adds the edited files in the same directory. 
    --input_path: The path to the root-directory where all the data files are stored. 
    --output_path: The path where the data should be be stored. If it says "same", it is stored in the same directory as
                   the original file with the ending <filename>_edited.txt 
    """

    parser = ArgumentParser()
    parser.add_argument('--input_path', type=str, required=True)
    parser.add_argument('--output_path', type=str, required=True)
    args = parser.parse_args()
    main(args.input_path, args.output_path)


