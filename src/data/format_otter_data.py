"""
This script formats data generated from Otter.AI
"""
from pathlib import Path

def find_tag(line):
    """Finds the tag of the current line. The tag is either emely or user"""
    is_tag = False
    if "emely: " in line:
        return True, "emely: "
    elif "user: " in line:
        return True, "user: "
    return is_tag, None

def find_text(line):
    is_text = True
    if "emely:" in line:
        return False
    elif "user:" in line:
        return False
    elif line == "\n":
        is_text = False
    return is_text


def editing(input_path, filename, output_path):
    """
    The main function for editing the Otter data so that it is in the correct format.
    --input_path: The path of the data including the file_name. The file_name must be a .txt
    --filename: The filename of the file that is stored.
    --output_path: The output path including the filename.  The file_name must be a .txt
    """

    file = open(input_path)
    lines = file.readlines()

    output = ""  # The output which is written into the file
    current_tag = ""  # The current conversation tag.

    for line in lines:
        # Find if the line contains a tag, and use this tag.
        is_tag, tag_temp = find_tag(line)
        if is_tag: current_tag = tag_temp
        # Test if the current line is a text. Append to the output if it is correct.
        is_text = find_text(line)
        # FIXME: Add a function that concatenates multiple entries from the same tag.
        if is_text:

                output += current_tag + line

    # Write the output file to the desired path.

    if not output_path.is_dir():
        output_path.mkdir(parents=True, exist_ok=True)

    print("Data used stored at: ".format(str(output_path) + filename))
    f = open(str(output_path) + filename, "w")
    f.write(output)
    f.close()





