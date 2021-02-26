"""
Class for doing translations.
"""

from googletrans import Translator
from deep_translator import GoogleTranslator

class TextTranslator():
    def __init__(self, languages):
        self.translator = Translator()
        self.deep_translator = self._create_deep_translator(languages)

    def _create_deep_translator(self, languages):
        translators = dict()
        for l1 in languages:
            for l2 in languages:
                #if l1 != l2:
                translators[l1 + l2] = GoogleTranslator(source=l1, target=l2)
        return translators


    def from_x_to_y_gt(self, text, l1, l2):
        """

        :param text: The text to translate
        :param l1: The first language
        :param l2: The second language.
        :return:
        """
        out = self.translator.translate(text, src=l1, dest=l2)
        return out.text

    def from_x_to_y_dt(self, text, source, dest):
        """
        Method to translate usign the deep translate function,
        :param text: The text to translate
        :param source: The source language
        :param dest: The destination language.
        :return:
        """


        return self.deep_translator[source + dest].translate(text)
