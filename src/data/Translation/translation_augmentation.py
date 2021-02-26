# A method for translating back and forth in order to augment data.

import pandas as pd
from pathlib import Path
import difflib

from translator import TextTranslator

# This function provides all Langugages that are supported by the deep_translate library.
# langs_list = GoogleTranslator.get_supported_languages(as_dict=True)


# English, German, French, Spanish, Latin, Esperanto.
languages = ["en", "de", "fr", "es", "eo", "it"]

text_translator = TextTranslator(languages)

# Define a list of languages that can be used for the translation


def translate_to_different_languages(text, src_language):
    """
    Translate the original sentence to different langugaes.
    :param text: The text to be translated
    :param src_language: The lagnguages of the text.
    :return: A dict with the original sentence is all languages.
    """
    output = dict()
    for l in languages:
        if not l == src_language:
            output[l] = text_translator.from_x_to_y_dt(text, src_language, l)

        else:
            output[src_language] = text
    return output

def test_text_similarity(data_base, text):
    """
    Checks if the new text is the same as a text that is already found in the database
    :return:
    """

    # Check if there any entries in the data_base to start with.
    if len(data_base)<1:
        return False
    else:
        # If there are entries, check the new text with respect to the old texts.
        for t in data_base:
            # Remove spaces so that if there is an extra space, it not used to differentiate between identical text.
            text1_trans = text.replace(" ", "")
            text2_trans = t.replace(" ", "")
            # If the equences are identical, return True
            if difflib.SequenceMatcher(None, text1_trans, text2_trans).ratio() == 1:
                return True
    return False



def translate_all_to_english(text_dict):
    """
    Translate all text to english and checks what text that should be added to the
    :param text_dict: A dictionary with sentences in different languages.
    :return:
    """

    outputs = []

    for src_1 in text_dict:
        for src_2 in text_dict[src_1]:
            # Check so that the languages are different.
            #if src_1 == src_2 and src_2 !="en":
            #    continue
            text = text_dict[src_1][src_2]

            text_en = text_translator.from_x_to_y_dt(text, src_2, "en")
            # Check if the current text is already in the database.
            if not test_text_similarity(outputs, text_en):
                outputs.append(text_en)
    return outputs

def run_augmentation(text, src_language="en"):
    """
    Runs the augmentation.
    :param text: The original text
    :param src_language: The language of the original text. It is assumed that the text are all in English.
    :return:
    """

    # Make an original translation of the text into different languages.
    sentences = translate_to_different_languages(text, src_language=src_language)

    text_dict = dict()

    # Go through all data in order to translate it to into other languages.
    for key in sentences:
        t = sentences[key]
        text_dict[key] = translate_to_different_languages(t, key)
    text_english = translate_all_to_english(text_dict)
    return text_english

def combine_source_and_target(data_dict, source_list, target_list, id):
    """
    Combines all the different sentences of source and target
    :param data_dict: The dict that is used to store the resulting data
    :param source_list: A list with the source texts
    :param target_list: A list with the target texts
    :param id:
    :return:
    """

    for src_m in range(len(source_list)):
        for target_m in range(len(target_list)):
            data_dict[id] = {"src": source_list[src_m], "target": target_list[target_m]}
            id += 1
    return id

def main(input_path: Path, output_path: Path):
    """
    The main method for augmenting data using the back and forth translation method.
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
        print("Working on text: {0}".format(k))
        # Extract source and targets texts.
        src = data_frame.iloc[k]["src"]

        target = data_frame.iloc[k]["target"]
        src_aug = run_augmentation(src)
        target_aug = run_augmentation(target)

        # Combine the different answers in order to create a uniqe set of data.
        # All these samples are unique.
        id = combine_source_and_target(output_dict, src_aug, target_aug, id)


    # Store the data.
    src_target_df = pd.DataFrame.from_dict(output_dict, orient='index')
    print("Storing data at: {0}".format(output_path))
    src_target_df.to_csv(output_path + "augmented_back_and_forth.csv", index_label='Name')
    # """

#"""
if __name__ == "__main__":
    path_ex = "..\\..\\..\\data\\processed\\interview_train.csv"
    path_out_ex = "..\\..\\..\\data\\augmented\\"
    main(path_ex, path_out_ex)
# """
