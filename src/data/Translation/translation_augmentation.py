# A method for translating back and forth in order to augment data.

import pandas as pd
from pathlib import Path
import difflib

from translator import TextTranslator
from argparse import ArgumentParser
from googletrans import Translator

from src.chat.translate import ChatTranslator
# This function provides all Langugages that are supported by the deep_translate library.
# langs_list = GoogleTranslator.get_supported_languages(as_dict=True)


# English, German, French, Spanish, Latin, Esperanto.
languages = ["en", "de", "fr", "es", "it"]

text_translator = TextTranslator(languages)
gtrans_translator = Translator()

# Define a list of languages that can be used for the translation


def translate_to_different_languages(text, src_language):
    """
    Translate the original sentence to different langugaes.
    :param text: The text to be translated
    :param src_language: The lagnguages of the text.
    :return: A dict with the original sentence is all languages.
    """
    output = dict()
    for dest in languages:
        if not dest == src_language:
            text_trans = text_translator.translate_text(text, src_language, dest)

            # Check so that the text is not a false statement.
            if text_trans:
                output[dest] = text_trans
            else:  # Deep translator didn't work, try googletrans
                alt_translation = gtrans_translator.translate(text, src=src_language, dest=dest)
                if text not in alt_translation:
                    output[dest] = alt_translation
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

            text = text_dict[src_1][src_2]
            # Translate the text.
            text_en = text_translator.translate_text(text, src_2, "en")
            # Check that the answer is not a False statement.
            if not text_en:
                continue

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


def combine_source_and_target(data_dict, source_list, target, index):
    """
    Combines all the different sentences of source and target
    :param data_dict: The dict that is used to store the resulting data
    :param source_list: A list with the source texts
    :param target: the target
    :param index:
    :return:
    """

    for src_m in range(len(source_list)):
        data_dict[index] = {"src": source_list[src_m], "target": target}
        index += 1
    return index


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

    data_frame = pd.read_csv(input_path)

    # Go through all the text in the csv file.
    M = data_frame.shape

    output_dict = {}
    index = 0
    for k in range(M[0]):
        print("Working on text: {0}".format(k))
        # Extract source and targets texts.
        src = data_frame.iloc[k]["src"]
        target = data_frame.iloc[k]["target"]

        # Find the user text in the src
        unmodified_src, user_text = src.rsplit('\n', 1)
        if user_text == '':
            unmodified_src, user_text = unmodified_src.rsplit('\n', 1)
            #
            # output_dict[index] = {"src": src, "target": target}
            # continue

        user_aug = run_augmentation(user_text)

        src_aug = []
        # Sometimes there are no translation variations
        if len(user_aug) == 1:
            print('did not translate: {}'.format(user_aug))
            src_aug.append(src)
        else:
        # Create a new src with the augmented user text
            for aug in user_aug:
                new_src = unmodified_src + '\n' + aug
                src_aug.append(new_src)

        # Combine the different answers in order to create a unique set of data.
        # All these samples are unique.
        index = combine_source_and_target(output_dict, src_aug, target, index)


    # Store the data.
    src_target_df = pd.DataFrame.from_dict(output_dict, orient='index')
    print("Storing data at: {0}".format(output_path))
    src_target_df.to_csv(output_path, index_label='Name')
    # """

#"""
if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('--data_file', type=str, required=True)
    args = parser.parse_args()

    data_dir = Path(__file__).resolve().parents[3].joinpath('data')
    path_ex = data_dir / 'processed' / args.data_file
    path_out_ex = data_dir / 'augmented' / args.data_file
    main(path_ex, path_out_ex)
# """
