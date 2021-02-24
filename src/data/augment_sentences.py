"""
Make a function that is used to augment sentences instead of of replacing words.
These data are stored in data\augmented\augmented_data.txt
It is in the same format as the data\raw\intervju_data.txt,
with the exception that the data are called source and target.
"""

import pandas as pd

import nltk
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')
from textaugment import Wordnet
t = Wordnet()


def augment_text(text):
    """
    Augments an entire text.
    :param text: The text that should be augmented.
    :return:
    """
    augmented_texts = []
    #Make several different augmentations.
    for k in range(5):
        augmented_texts.append(t.augment(text))

    return augmented_texts


def main(path):
    #

    data_frame = pd.read_csv(path)

    # Go through all the text in the

    M = data_frame.shape

    output_text = ""

    for k in range(M[0]):
        # Extract
        src = data_frame.iloc[k]["src"]
        # find_special_characters(src)

        target = data_frame.iloc[k]["target"]

        src_aug = augment_text(src)
        target_aug = augment_text(target)

        # Combine all the combinations of augmentations from the source and the taget data.
        for k1 in range(len(src_aug)):
            for k2 in range(len(target_aug)):
                output_text += "source: {0}\ntarget: {1}\nepisode_done \n \n".format(src_aug[k1], target_aug[k2])

    save_path = "data\\augmented\\"

    file1 = open(save_path + "augmented_data.txt", "w")
    file1.write(output_text)
    file1.close()


if __name__ == "__main__":
    path = "C:\\Users\\WilliamRosengren\\Documents\\Jobb\\Freja\\freja\\data\\processed\\interview_train.csv"

    main(path)







