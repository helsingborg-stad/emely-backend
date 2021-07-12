import six
from google.cloud import translate_v2 as translate
import os
from pathlib import Path
import re
from src.api.utils import is_gcp_instance

""" Translates text using Google's official API
"""

class ChatTranslator:

    def __init__(self):

        # Set this to your google api key location
        if not is_gcp_instance():
            # Add an authentication to the Google translate if we are not on GCP.
            json_path = Path(__file__).resolve().parents[2].joinpath('emelybrainapi-33194bec3069.json')
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = json_path.as_posix()

        # Translator object
        self.gcloud_translator = translate.Client()
        # logging.basicConfig(filename='translate.log', level=logging.WARNING, format='%(levelname)s - %(message)s')
        self.nbr_translation = 0

    def translate(self, text : str, src: str, target: str) -> str:
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

        text = self._model_output_corrections(text)

        if isinstance(text, six.binary_type):
            text = text.decode("utf-8")
        result = self.gcloud_translator.translate(text, source_language=src, target_language=target)
        trans = result['translatedText']
        
        # Matching spaces between word and delimiters ,.?!
        # and then removing the spaces
        trans = re.sub(r'\s(?=[^,\s\w+]*[,.?!])', "", trans)
        
        # Fixes upper and lowercase letters at the beginning of each sentence
        trans = re.sub(r'(^[a-zåäöA-Zåäö]|(?<=[?.!]\s)\w)', lambda match: r'{}'.format(match.group(1).upper()), trans)
        return trans
        
    def _model_output_corrections(self, message: str) -> str:
        """[summary]

        Args:
            message (str): [description]

        Returns:
            str: [description]
        """
        file_path = Path(__file__).parent.joinpath('swenglish.txt')
        with open(file_path, "r") as f:
            swenglish_phrases = f.readlines()
        for phrase in swenglish_phrases:
            eng, swe = phrase.split(":")[0].strip(), phrase.split(":")[1].strip()
            if eng.lower() in message.lower():
                message = message.replace(eng, swe)
        return message
