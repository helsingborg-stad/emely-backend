"""
Class for doing translations.
"""

from googletrans import Translator
from deep_translator import GoogleTranslator

class TextTranslator():
    def __init__(self, languages):
        self.translator = Translator()
        self.deep_translator = self._create_deep_translator(languages)
        self.try_deep_trans = True # Marker to determine the translation API.

    def _create_deep_translator(self, languages):
        translators = dict()
        for l1 in languages:
            for l2 in languages:
                #if l1 != l2:
                translators[l1 + l2] = GoogleTranslator(source=l1, target=l2)
        return translators


    def from_x_to_y_gt(self, text, source, dest):
        """

        :param text: The text to translate
        :param source: The source language
        :param dest: The destination language.
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

    def try_translate(self, text, source, dest):
        if self.try_deep_trans:
            text = self.from_x_to_y_dt(text, source, dest)
        else:
            text = self.from_x_to_y_gt(text, source, dest)
        return text


    def translate_text(self, text, source, dest, maximum_try=5):
        """
        Function that is used to translate the text. If it does not work, it tries to use another method.
        :param text: The text that should be translated
        :param source: The source language, i.e., the same language as the text
        :param dest: The translated text.
        :param maximum_try: The maximum number of times that the translation is tried.
        :return: The translated text
        """

        try_index = 0

        while try_index < maximum_try:
            # Try to translate the text.
            try:
                text = self.try_translate(text, source, dest)
                return text
            # If that does not work, try a the other method,
            except:
                try_index += 1
                if self.try_deep_trans:
                    self.try_deep_trans = False
                else:
                    self.try_deep_trans = True
        # If nothing of that works, return a false statement.
        return False