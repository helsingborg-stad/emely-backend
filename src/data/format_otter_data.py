"""
This script formats data generated from Otter.AI
"""

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


def editing(input_path, output_path):
    """
    The main function for editing the Otter data so that it is in the correct format.
    --input_path: The path of the data including the file_name. The file_name must be a .txt
    --output_path: The output path including the filename.  The file_name must be a .txt
    """

    file = open(input_path)
    lines = file.readlines()

    output = ""  # The output which is written into the file
    current_tag = ""  # The current conversation tag.
    last_tag = ""  # The last conversation tag. If this is the same as the last conversation tag,
                   # the current line without the tag should be appended.
    for line in lines:
        # Find if the line contains a tag, and use this tag.
        is_tag, tag_temp = find_tag(line)
        if is_tag: current_tag = tag_temp
        # Test if the current line is a text. Append to the output if it is correct.
        is_text = find_text(line)
        # FIXME: Add a function that concatenates multiple entries from the same tag.
        if is_text:
            #if current_tag == last_tag:
            #    print("if")
            #output += line.replace("\n", "")
            #else:
            #    print("else")
                output += current_tag + line
        # Update the last tag.
        if current_tag is not None:
            last_tag = current_tag

    # Write the output file to the desired path.
    f = open(output_path, "w")
    f.write(output)






