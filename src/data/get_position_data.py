import pandas as pd
from pathlib import Path





def extact_data(line_list):
    """
    Extracts the data for a conversation.
    :return:
    """
    is_first = True

    source = ""

    for l in line_list:

        if "emely:" in l and is_first:
            is_first = False
            source += l.replace("emely:", "")
        elif "emely:" in l and not is_first:

            target = l.replace("emely:", "")
            return target, source
        elif "user" in l:
            source += l.replace("user: ", "")

def run_data_extraction(lines, output_path):

    current_lines = []

    output = {}
    counter = 0
    for k, line in enumerate(lines):
        # Test if there there is a new position

        if "=" in line:
            continue
        current_lines.append(line)

        if "episode_done" in line:
            # If the episode is done add the data

            target, source = extact_data(current_lines)

            output[counter] = {"target": target, "src": source}
            counter += 1
            print("counter {0}".format(counter))
            current_lines = []
            append_lines = True

    src_target_df = pd.DataFrame.from_dict(output, orient='index')

    src_target_df.to_csv(output_path + "position_data.csv", index_label='Name')
    print("The data has been stored at: {0}".format(output_path + "position_data.csv"))

def main():
    # The path for the rawdata must be here.
    path = "..\\..\\data\\raw\\position_data.txt"
    # Read the lines.
    with open(path) as fp:
        lines = fp.readlines()
    # Check if the output path exsits.
    output_path = "..\\..\\data\\processed\\"
    p = Path(output_path)
    # If not, create the path.
    if not p.exists():
        Path(output_path).mkdir(parents=True, exist_ok=True)
    run_data_extraction(lines, output_path)


if __name__ == "__main__":
    main()