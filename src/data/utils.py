"""
Utilities used by ultiple scripts in src/data
"""

import codecs
from pathlib import Path

def store_as_txt(text, output_path):
    """Saves the translated data in a new .txt-file
       --text: The new text that are to be stored.
       --output_path: The path where the data is stored. This is a stribng

    """

    f = open(output_path, "w")
    f.write(text)
    f.close()


def open_with_errors(input_path):
    """Is able to open files even if there are errors in the file. """

    with codecs.open(input_path, 'r', encoding='utf-8', errors='ignore') as fdata:
        data = fdata.readlines()
    return data

def remove_json(path: Path):
    """ Removes all .json files in the Path path. This is used in order to not create duplicates"""

    for p in path.glob('**/*'):
        if ".json" in str(p):
            p.unlink()
            print("Removed file: {0}".format(str(p)))