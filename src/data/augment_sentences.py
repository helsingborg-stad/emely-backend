"""
Make a function that is used to augment sentences instead of of replacing words.
These data are stored in data\augmented\augmented_data.txt
It is in the same format as the data\raw\intervju_data.txt,
with the exception that the data are called source and target.
"""

import pandas as pd

import nltk

from pathlib import Path

nltk.download('punkt')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')
from textaugment import Wordnet
t = Wordnet()

# TODO: Fix the paths.

def augment_text(text, nbr_of_iterations=1):
    """
    Augments an entire text.
    :param text: The text that should be augmented. In the case of Freja, this is either one instance of a source
                  or a target text.
    :param nbr_of_iterations: The number of iterations to run the data augmentation for a given text.
    :return:
    """
    augmented_texts = []
    #Make several different augmentations for the same text.
    for k in range(nbr_of_iterations):
        augmented_texts.append(t.augment(text))

    return augmented_texts


def main(input_path: Path, output_path: Path):
    """
    The main method for augmenting data using
    :param input_path:
    :param output_path:
    :return:
    """

    # Check if the path exists.
    p = Path(output_path)
    # If not, create the path.
    if not p.exists():
        Path(output_path).mkdir(parents=True, exist_ok=True)

    data_frame = pd.read_csv(input_path)

    # Go through all the text in the csv file.

    M = data_frame.shape

    output_dict = {}
    id = 0
    for k in range(M[0]):
        # Extract source and targets texts. 
        src = data_frame.iloc[k]["src"]

        target = data_frame.iloc[k]["target"]

        src_aug = augment_text(src)
        target_aug = augment_text(target)

        # Combine all the combinations of augmentations from the source and the taget data.
        for k1 in range(len(src_aug)):
            for k2 in range(len(target_aug)):
                output_dict[id] = {"src": src_aug[k1], "target": target_aug[k2]}
                id += 1

    src_target_df = pd.DataFrame.from_dict(output_dict, orient='index')
    print("Storing data at: {0}".format(output_dict))
    src_target_df.to_csv(output_path + "augmented_data.csv", index_label='Name')


#"""
if __name__ == "__main__":
    path_ex = "..\\..\\data\\processed\\interview_train.csv"
    path_out_ex = "..\\..\\data\\augmented\\"
    main(path_ex, path_out_ex)
# """







