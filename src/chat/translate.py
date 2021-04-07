from deep_translator import GoogleTranslator
from googletrans import Translator
import six
from google.cloud import translate_v2 as translate

import logging
import os
from pathlib import Path

from src.api.utils import is_gcp_instance

class ChatTranslator:

    def __init__(self, default_translator='googletrans'):
        # Set this to your google api key location
        if is_gcp_instance():
            # Add a authentication to the Google translate.
            pass

        else:
            json_path = Path(__file__).resolve().parents[2].joinpath('emelybrainapi-33194bec3069.json')
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = json_path.as_posix()

        # Translator objects
        self.default = default_translator
        self.deeptranslator_en_to_sv = GoogleTranslator(source='en', target='sv')
        self.deeptranslator_sv_to_en = GoogleTranslator(source='sv', target='en')
        self.gtrans_translator = Translator()
        self.gcloud_translator = translate.Client()
        logging.basicConfig(filename='translate.log', level=logging.WARNING, format='%(levelname)s - %(message)s')
        self.nbr_translation = 0

    def translate(self, text, src, target, package=None):
        if package is None:
            package = self.default

        if package == 'gcloud':
            return self.gcloud_translate(text, src, target)
        elif package == 'googletrans':
            try:
                return self.gtrans_translate(text, src, target)
            except:
                return self.gcloud_translate(text, src, target)
        elif package == 'deep_translator':
            try:
                return self.deep_translate(text, src, target)
            except:
                return self.gcloud_translate(text, src, target)
        else:
            raise ValueError('No package named{}'.format(package))

    def gcloud_translate(self, text, src, target):
        """Uses official google translate API.
        Configure your credentials in conda environment using
        $conda env config vars set GOOGLE_APPLICATION_CREDENTIALS=path/to/json """
        if isinstance(text, six.binary_type):
            text = text.decode("utf-8")

        result = self.gcloud_translator.translate(text, source_language=src, target_language=target)
        return result['translatedText']

    def gtrans_translate(self, text, src, target):
        """Uses googletrans package for translation. Raises warning if translation i unsuccesful"""
        assert src == 'sv' or src == 'en'
        assert target == 'sv' or target == 'en'
        out = self.gtrans_translator.translate(text, src=src, dest=target)
        translated_text = out.text
        if translated_text == text:
            msg = 'googletrans failed'
            logging.warning(msg)
            raise Warning(msg)
        else:
            return translated_text

    def deep_translate(self, text, src, target):
        """Uses deep translator to translate text. If the service is down we raise a warning
        to allow the program to use the official google cloud api instead"""
        # Needed to compare translation result to original string
        if text[0] == ' ':
            text = text[1:]

        if src == 'sv' and target == 'en':
            translation = self.deeptranslator_sv_to_en.translate(text)
            if translation == text:
                msg = 'deep_translator failed'
                logging.warning(msg)
                raise Warning(msg)
            else:
                return translation
        elif src == 'en' and target == 'sv':
            translation = self.deeptranslator_en_to_sv.translate(text)
            if translation == text:
                msg = 'deep_translator failed'
                logging.warning(msg)
                raise Warning(msg)
            else:
                return translation
        else:
            raise ValueError('One or more invalid language code\n src:{}\n target:{}'.format(src, target))
