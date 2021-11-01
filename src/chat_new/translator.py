import six
from google.cloud import translate_v2 as translate
import os
from pathlib import Path
import re
from src.api.utils import is_gcp_instance
from utils import timer
from aioify import aioify

""" Translates text using Google's official API
"""


class ChatTranslator:
    def __init__(self):

        # Set this to your google api key location
        if not is_gcp_instance():
            # Add an authentication to the Google translate if we are not on GCP.
            json_path = (
                Path(__file__)
                .resolve()
                .parents[2]
                .joinpath("emelybrainapi-33194bec3069.json")
            )
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = json_path.as_posix()

        # Translator object
        self.gcloud_translator = translate.Client()
        self.swenglish_dict = self._load_swenglish()

    @aioify
    def translate(self, text: str, src: str, target: str) -> str:
        """
        @ Isabella - Method that translates between two languages
        and makes sure each start of sentence is uppercase

        Args:
            text (str): text that is to be translated
            src (str): source language of text string
            target (str): target language of text string

        Returns:
            str: the translated string
        """
        # To minimize errors in google translate - lowercase everything
        text = text.lower()

        if isinstance(text, six.binary_type):
            text = text.decode("utf-8")
        result = self.gcloud_translator.translate(
            text, source_language=src, target_language=target, format_="text"
        )
        translated_text = result["translatedText"]

        if src == "en" and target == "sv":
            translated_text = self.correct_swenglish(translated_text)

        translated_text = self.format_text(translated_text)

        return translated_text

    def format_text(self, text: str) -> str:
        "Fixes some common formatting errors produced by the blenderbot and translate"
        # Matching spaces between word and delimiters ,.?!
        # and then removing the spaces
        text = re.sub(r"\s(?=[^,\s\w+]*[,.?!])", "", text)

        # Fixes upper and lowercase letters at the beginning of each sentence
        text = re.sub(
            r"(^[a-zåäöA-Zåäö]|(?<=[?.!]\s)\w)",
            lambda match: r"{}".format(match.group(1).upper()),
            text,
        )
        return text

    def _load_swenglish(self) -> dict:
        "Reads common swenglish translations from file to dictionary"
        p = Path(__file__).parent / "swenglish.txt"
        with open(p, "r") as f:
            swenglish_phrases = f.readlines()

        dictionary = {}
        for phrase in swenglish_phrases:
            phrase = phrase.lower()
            eng, swe = phrase.split(":")
            dictionary[eng.strip()] = swe.strip()

        return dictionary

    def correct_swenglish(self, text: str) -> str:
        "Corrects text if it contains swenglish"
        text = text.lower()

        for eng_phrase, swe_phrase in self.swenglish_dict.items():
            if eng_phrase in text:
                text = text.replace(eng_phrase, swe_phrase)
        return text
