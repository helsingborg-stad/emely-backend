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
        self.max_translations = 70
        logging.basicConfig(filename='translate.log', level=logging.WARNING, format='%(levelname)s - %(message)s')

    def reset_conversation(self):
        self.conversation_sv.reset()
        self.conversation_en.reset()
        return

    def chat(self, user_input):
        self.observe(user_input)
        if not self.episode_done:
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
        while translated_text == text and i < self.max_translations:
            # Try translating again and alternate between translators until something works or timeout
            if i % 2 == 0:
                try:
                    translated_text = self.translator_sv_to_en.translate(text)
                except KeyError:
                    pass
            else:
                out = self.general_translator.translate(text, src='sv', dest='en')
                translated_text = out.text
            i += 1

        # Logging
        if i > 0:
            if i == self.max_translations:
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
        while translated_text == text and i < self.max_translations:
            # Try translating again
            if i % 2 == 0:
                try:
                    translated_text = self.translator_en_to_sv.translate(text)
                except KeyError:
                    pass
            else:
                out = self.general_translator.translate(text, src='en', dest='sv')
                translated_text = out.text
            i += 1

        # Logging
        if i > 0:
            if i == self.max_translations:
                outcome = 'Failure'
            elif i % 2 == 0:
                outcome = 'success with deep_translator'
            else:
                outcome = 'success with googletrans'
            logging.warning('Failure to translate english to swedish. Tried {} times. Outcome: {}'.format(i, outcome))
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

    def start(self, session_id, name, job):
        # TODO: Prompt the user to add name and job they're looking for with api
        return

    def observe(self, user_input):
        # TODO: Is question? We don't want to reply to a question with a question. if is_question: reply model_answer + interview_question
        # TODO: Better check of input stop
        # Observe the user input, translate and update internal states.
        # We assume the user_input is always grammatically correct!

        translated_input = self._sv_to_en(user_input)
        self.conversation_sv.add_user_text(user_input)
        self.conversation_en.add_user_text(translated_input)

        # Set episode done if exit condtion is met.
        if self.nbr_replies == self.max_replies and len(self.questions) == 0 or user_input.lower().replace(' ',
                                                                                                           '') in self.stop_tokens:
            self.episode_done = True

        return

    def act(self):
        # If it's time for another interview question, we don't need to pass anything through the mode
        if self.episode_done:
            self.save()
            self.reset_conversation()
            bye = 'Tack för din tid, det var trevligt att få intervjua dig!'
            print(bye)
            return bye
        elif self.nbr_replies == self.max_replies:
            self.nbr_replies = 0
            interview_question = self.questions.pop()
            interview_question_en = self._sv_to_en(interview_question)
            self.conversation_sv.add_bot_text(interview_question)
            self.conversation_en.add_bot_text(interview_question_en)
            print(interview_question)
            return interview_question
        else:
            context = self._get_context()
            inputs = self.tokenizer([context], return_tensors='pt')
            inputs.to(self.device)
            with no_grad():
                output_tokens = self.model.generate(**inputs)
                reply_en = self.tokenizer.decode(output_tokens[0], skip_special_tokens=True)

            reply_en = self._correct_reply(reply_en)
            # _correct_reply can return empty string -> force new question
            if len(reply_en) < 3:
                self.nbr_replies = 0
                try:
                    reply_sv = self.questions.pop()
                    reply_en = self._sv_to_en(reply_sv)
                except IndexError:
                    reply_en = 'Thank you for your time. We will keep in touch'
                    reply_sv = 'Tack för din tid, det var trevligt att få intervjua dig!'
                    self.episode_done = True
            else:
                self.nbr_replies += 1
                reply_sv = self._en_to_sv(reply_en)
            print(reply_sv)
            self.conversation_sv.add_bot_text(reply_sv)
            self.conversation_en.add_bot_text(reply_en)
            return reply_sv


    def _get_context(self):
        # persona + dialogue history
        return self.persona + '\n' + self.conversation_en.get_dialogue_history(125 - self.persona_length)

    def _correct_reply(self, reply):
        # For every bot reply, check what sentences are repetitive and remove that part only.
        # Current check will discard a sentence where she asks something new but with a little detail
        previous_replies = self.conversation_en.get_bot_replies()

        if len(previous_replies) == 0:
            return reply
        previous_sentences = []

        # Split sentences and keep separators
        sentence_splits = re.split('([.?!])', reply)
        if sentence_splits[-1] == '':
            del sentence_splits[-1]
        sentences = [sep for i, sep in enumerate(sentence_splits) if i % 2 == 0]
        separators = [sep for i, sep in enumerate(sentence_splits) if i % 2 != 0]


        for old_reply in previous_replies:
            raw_splits = re.split('[.?!]', old_reply)
            splits = [s for s in raw_splits if len(s) > 2]
            previous_sentences.extend(splits)

        keep_idx = []
        # For each part/sentence of the new reply, save it if it's not close to something said before
        for i in range(len(sentences)):
            combos = list(product([sentences[i]], previous_sentences))
            ratios = [SequenceMatcher(a=s1, b=s2).ratio() for s1, s2 in combos]
            if max(ratios) < 0.5:
                keep_idx.append(i)

        # Freja cannot say that she's also a {job}
        frejas_lie = 'I am a {}'.format(self.job)
        temp_idx = []
        for i in keep_idx:
            lie_prob = SequenceMatcher(a=frejas_lie, b=sentences[i]).ratio()
            if lie_prob < 0.75:
                temp_idx.append(i)
            else:
                logging.warning('Identified lie removed: {}'.format(frejas_lie))
        keep_idx = temp_idx


        if len(keep_idx) == len(sentences):  # Everything is fresh and we return it unmodified
            return reply
        else:
            new_reply = ''
            for i in keep_idx:
                try:
                    new_reply = new_reply + sentences[i] + separators[i] + ' '
                except IndexError:
                    new_reply = new_reply + sentences[i]
            if len(new_reply) > 3:
                logging.warning('Corrected: {} \n to: {}'.format(reply, new_reply))
            return new_reply


def read_questions(file_path):
    # Reads interview questions from a text file, one question per line. '{}' in place where job should be inserted
    with open(file_path, 'r') as f:
        questions = f.readlines()
    format_this = [True if '{}' in question else False for question in questions]
    return zip(questions, format_this)
