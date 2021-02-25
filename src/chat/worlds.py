from deep_translator import GoogleTranslator
from googletrans import Translator
from transformers import BlenderbotTokenizer, BlenderbotForConditionalGeneration, BlenderbotSmallTokenizer, \
    BlenderbotSmallForConditionalGeneration
from torch import no_grad
import torch
import random
from conversation import BlenderConversation
import re
from itertools import product
from difflib import SequenceMatcher

import time
import logging


class ChatWorld:
    # Class that keeps

    def __init__(self, mname='facebook/blenderbot-400M-distill'):
        # TODO: init model and tokenizer from file
        # TODO: init from opt like dictionary

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        if 'small' in mname:
            self.model = BlenderbotSmallForConditionalGeneration.from_pretrained(mname)
            self.tokenizer = BlenderbotSmallTokenizer.from_pretrained(mname)
        else:
            self.model = BlenderbotForConditionalGeneration.from_pretrained(mname)
            self.tokenizer = BlenderbotTokenizer.from_pretrained(mname)

        self.model.to(self.device)

        self.model_name = mname.replace('facebook/', '')
        self.translator_en_to_sv = GoogleTranslator(source='en', target='sv')
        self.translator_sv_to_en = GoogleTranslator(source='sv', target='en')
        self.general_translator = Translator()
        self.episode_done = False
        self.stop_tokens = ['färdig', 'slut', 'hejdå', 'done']  # TODO: Snyggare lösning krävs

        self.conversation_sv = BlenderConversation(lang='sv', tokenizer=self.tokenizer)
        self.conversation_en = BlenderConversation(lang='en', tokenizer=self.tokenizer)
        self.description = 'Open dialogue with {}'.format(self.model_name)

        # Used for logging translation problems
        logging.basicConfig(filemode='translate.log', level=logging.WARNING, format='%(levelname)s - %(message)s')

    def reset_conversation(self):
        self.conversation_sv.reset()
        self.conversation_en.reset()
        return

    def chat(self, user_input):
        self.observe(user_input)
        self.act()
        return

    def save(self, error=None):
        self.conversation_sv.to_txt(self.description, 'chat_output/interview_dialogue.txt', error=error)
        self.conversation_en.to_txt('English ' + self.description, 'chat_output/interview_dialogue.txt', error=error)
        return

    def observe(self, user_input):
        # TODO: Add spell check/grammar check here
        # Observe the user input, translate and update internal states
        # Check if user wants to quit/no questions left --> self.episode_done = True

        translated_input = self._sv_to_en(user_input)
        self.conversation_sv.add_user_text(user_input)
        self.conversation_en.add_user_text(translated_input)

        # Set episode done if exit condition is met. TODO: Better check of input stop
        if user_input.lower().replace(' ', '') in self.stop_tokens:
            self.episode_done = True
        return

    def act(self):
        if not self.episode_done:
            context = self._get_context()
            inputs = self.tokenizer([context], return_tensors='pt')
            inputs.to(self.device)
            with no_grad():
                output_tokens = self.model.generate(**inputs)
            reply = self.tokenizer.decode(output_tokens[0], skip_special_tokens=True)

            translated_reply = self._en_to_sv(reply)
            self.conversation_sv.add_bot_text(translated_reply)
            self.conversation_en.add_bot_text(reply)
            self.conversation_sv.print_dialogue()

        else:
            self.conversation_sv.to_txt(self.description, 'chat_output/open_dialogue.txt')
            self.conversation_en.to_txt(self.description, 'chat_output/open_dialogue.txt')
            print('Kul att prata med dig! Hejdå!')
        return

    def _get_context(self):
        context = self.conversation_en.get_dialogue_history()
        return context

    def _validate_reply(self, answer):
        return True

    # TODO: try: googletrans except: googles official API
    def _sv_to_en(self, text):
        """Alternates between googletrans and deep_translate packages to solve failure to translate """
        if text[0] == ' ':
            text = text[1:]
        out = self.general_translator.translate(text, src='sv', dest='en')
        translated_text = out.text
        i = 0
        while translated_text == text and i < 20:
            # Try translating again and alternate between translators until something works or timeout
            if i % 2 == 0:
                translated_text = self.translator_sv_to_en.translate(text)
            else:
                out = self.general_translator.translate(text, src='sv', dest='en')
                translated_text = out.text
            i += 1

        # Logging
        if i > 0:
            if i == 20:
                outcome = 'Failure'
            elif i % 2 == 0:
                outcome = 'success with deep_translator'
            else:
                outcome = 'success with googletrans'
            logging.warning('Failure to translate swedish to english. Tried {} times. Outcome: {}'.format(i, outcome))

        return translated_text

    def _en_to_sv(self, text):
        """Alternates between googletrans and deep_translate packages to solve failure to translate """
        if text[0] == ' ':
            text = text[1:]
        out = self.general_translator.translate(text, src='en', dest='sv')
        translated_text = out.text
        i = 0
        while translated_text == text and i < 20:
            # Try translating again
            if i % 2 == 0:
                translated_text = self.translator_en_to_sv.translate(text)
            else:
                out = self.general_translator.translate(text, src='en', dest='sv')
                translated_text = out.text
            i += 1

        # Logging
        if i > 0:
            if i == 20:
                outcome = 'Failure'
            elif i % 2 == 0:
                outcome = 'success with deep_translator'
            else:
                outcome = 'success with googletrans'
            logging.warning('Failure to translate swedish to english. Tried {} times. Outcome: {}'.format(i, outcome))

        return translated_text


class InterviewWorld(ChatWorld):
    # Class that keeps
    def __init__(self, job, name, mname='facebook/blenderbot-400M-distill'):
        # TODO: More sophisticated questions/greeting drawn from txt file(?) and formated with name and job
        # TODO: init model and tokenizer from file
        # TODO: init from opt like dictionary
        super().__init__(mname)

        self.questions = [question.format(job) if format_this else question for (question, format_this) in
                          read_questions('interview_questions.txt')]
        random.shuffle(self.questions)
        self.greeting = 'Hej, och välkommen till din intervju. Hur står det till, {}?'.format(name)

        self.job = job
        self.human_name = name
        self.stop_tokens = ['färdig', 'slut', 'hejdå', 'done']  # TODO: Snyggare lösning
        self.max_replies = 2  # Maximum number of replies back and forth for each question
        self.nbr_replies = 0
        self.description = 'InterviewWorld\t job: {}\t name: {}\t model: {}'.format(self.job, self.human_name,
                                                                                    self.model_name)

        self.greet()
        self.init_context()

    def init_context(self):
        # TODO: Pull persona from txt file or something
        self.persona = 'your persona: I have worked for this company for five years\nyour persona: I work in HR\nyour persona: I want to know more about you\nyour persona: I will ask you more questions'
        self.persona_length = len(self.tokenizer(self.persona)['input_ids'])
        return

    def greet(self):
        print(self.greeting)
        return

    def start(self):
        # TODO: Prompt the user to add name and job they're looking for?
        return

    def observe(self, user_input):
        # TODO: Add spell check/grammar check here
        # TODO: Is question? We don't want to reply to a question with a question. if is_question: reply model_answer + interview_question
        # TODO: Better check of input stop
        # Observe the user input, translate and update internal states

        translated_input = self._sv_to_en(user_input)
        self.conversation_sv.add_user_text(user_input)
        self.conversation_en.add_user_text(translated_input)

        # Set episode done if exit conidion is met.
        if self.nbr_replies == self.max_replies and len(self.questions) == 0 or user_input.lower().replace(' ',
                                                                                                           '') in self.stop_tokens:
            self.episode_done = True

        return

    def act(self):
        if not self.episode_done:
            context = self._get_context()
            inputs = self.tokenizer([context], return_tensors='pt')
            inputs.to(self.device)
            with no_grad():
                output_tokens = self.model.generate(**inputs)
            reply_en = self.tokenizer.decode(output_tokens[0], skip_special_tokens=True)

            if self._validate_reply(reply_en) and self.nbr_replies < self.max_replies:
                self.nbr_replies += 1
                reply_sv = self._en_to_sv(reply_en)
            else:
                # TODO: More tries here? Change context or something
                warning = 'I generated a repetitive answer: {}'.format(reply_en)
                logging.warning(warning)
                try:
                    reply_sv = self.questions.pop()
                    reply_en = self.translator_sv_to_en.translate(reply_sv)
                except:
                    reply_en = 'Thank you for your time. We will keep in touch'
                    reply_sv = 'Tack för din tid, det var trevligt att få intervjua dig!'
                self.nbr_replies = 0

            print(reply_sv)
            self.conversation_sv.add_bot_text(reply_sv)
            self.conversation_en.add_bot_text(reply_en)
        else:
            self.save()
            print('Tack för din tid, det var trevligt att få intervjua dig!')
        return

    def _get_context(self):
        # persona + dialogue history
        return self.persona + '\n' + self.conversation_en.get_dialogue_history(125 - self.persona_length)

    def _validate_reply(self, reply):
        # TODO:
        previous_replies = self.conversation_en.get_bot_replies()

        if len(previous_replies) == 0:
            return True
        previous_sentences = []

        # Split sentences, remove unwanted artefacts like empty strings, create permutations, and check argmax of ratio of all elements
        sentences = re.split('[.?!]', reply)
        for old_reply in previous_replies:
            raw_splits = re.split('[.?!]', old_reply)
            splits = [s for s in raw_splits if len(s) > 2]
            previous_sentences.extend(splits)

        combos = list(product(sentences, previous_sentences))
        ratios = [SequenceMatcher(a=s1, b=s2).ratio() for s1, s2 in combos]
        if max(ratios) > 0.75:
            return False
        else:
            return True


class InterviewWorld2(InterviewWorld):

    def __init__(self, job, name, mname='facebook/blenderbot-400M-distill'):
        super(InterviewWorld2, self).__init__(job, name, mname=mname)

    # TODO: Implement another version
    def _validate_reply(self, reply):
        # Overrides the previous
        # For every bot reply, check what sentences are repetitive and remove that part only.
        # Current check will discard a sentence where she asks something new but with a little detail
        return True


def read_questions(file_path):
    # Reads interview questions from a text file, one question per line. '{}' in place where job should be inserted
    with open(file_path, 'r') as f:
        questions = f.readlines()
    format_this = [True if '{}' in question else False for question in questions]
    return zip(questions, format_this)
