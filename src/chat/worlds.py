from transformers import BlenderbotTokenizer, BlenderbotForConditionalGeneration, BlenderbotSmallTokenizer, \
    BlenderbotSmallForConditionalGeneration
from torch import no_grad
import torch
import random
from src.chat.conversation import BlenderConversation
from src.chat.translate import ChatTranslator

import re
from itertools import product
from difflib import SequenceMatcher

import logging
from pathlib import Path


class ChatWorld:
    # Class that keeps

    def __init__(self, **kwargs):
        # TODO: init model and tokenizer from file
        # TODO: init from opt like dictionary

        self.model_name = kwargs['model_name']
        self.local_model = kwargs['local_model']
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.tokenizer = None
        self.model_loaded = False

        self.translator = ChatTranslator()

        self.episode_done = {}
        self.persona = None
        self.persona_length = 0
        self.stop_tokens = ['hejdå', 'bye', 'hej då']  # TODO: More sophisticated solution

        self.conversations_sv = {}
        self.conversations_en = {}

        # self.conversation_sv = BlenderConversation(lang='sv', tokenizer=self.tokenizer)
        # self.conversation_en = BlenderConversation(lang='en', tokenizer=self.tokenizer)
        # self.description = 'Open dialogue with {}'.format(self.model_name)

        logging.basicConfig(filename='worlds.log', level=logging.WARNING, format='%(levelname)s - %(message)s')

    def load_model(self):
        """Loads model from huggingface or locally. Works with both BlenderbotSmall and regular"""
        # TODO: Add some checks here for if the local model exists and if the user mistakenly adds local_model=True
        if self.local_model:
            model_dir = Path(__file__).parents[2] / 'models' / self.model_name / 'model'
            token_dir = Path(__file__).parents[2] / 'models' / self.model_name / 'tokenizer'
            assert model_dir.exists() and token_dir.exists()
        elif 'facebook/' in self.model_name:
            model_dir = self.model_name
            token_dir = self.model_name
        else:
            self.model_loaded = False

        if 'small' in self.model_name:
            self.model = BlenderbotSmallForConditionalGeneration.from_pretrained(model_dir)
            self.tokenizer = BlenderbotSmallTokenizer.from_pretrained(token_dir)
        else:
            self.model = BlenderbotForConditionalGeneration.from_pretrained(model_dir)
            self.tokenizer = BlenderbotTokenizer.from_pretrained(token_dir)

        self.model.to(self.device)
        self.model_loaded = True
        return

    def unload_model(self):
        self.model = None
        self.tokenizer = None
        self.model_loaded = False
        return

    def reset_conversation(self, conversation_id):
        self.conversations_en[conversation_id].reset()
        self.conversations_sv[conversation_id].reset()
        return

    def chat(self, user_input, conversation_id):
        self.observe(user_input, conversation_id)
        if not self.episode_done[conversation_id]:
            reply = self.act(conversation_id)
        return reply

    # def save(self, error=None):
    #     self.conversation_sv.to_txt(self.description, 'chat_output/interview_dialogue.txt', error=error)
    #     self.conversation_en.to_txt('English ' + self.description, 'chat_output/interview_dialogue.txt', error=error)
    #     return

    def observe(self, user_input, conversation_id):
        # TODO: Add spell check/grammar check here
        # Observe the user input, translate and update internal states
        # Check if user wants to quit/no questions left --> self.episode_done = True

        translated_input = self.translator.translate(user_input, src='sv', target='en')
        self.conversations_sv[conversation_id].add_user_text(user_input)
        self.conversations_en[conversation_id].add_user_text(translated_input)

        # Set episode done if exit condition is met. TODO: Better check of input stop
        if user_input.lower().replace(' ', '') in self.stop_tokens:
            self.episode_done[conversation_id] = True
        return self.episode_done[conversation_id]

    def act(self, conversation_id):
        if not self.episode_done[conversation_id]:
            context = self._get_context(conversation_id)
            inputs = self.tokenizer([context], return_tensors='pt')
            inputs.to(self.device)
            with no_grad():
                output_tokens = self.model.generate(**inputs)
            reply = self.tokenizer.decode(output_tokens[0], skip_special_tokens=True)

            reply_sv = self.translator.translate(reply, src='en', target='sv')
            self.conversations_sv[conversation_id].add_bot_text(reply_sv)
            self.conversations_en[conversation_id].add_bot_text(reply)
            return reply_sv

        else:
            return 'Kul att prata med dig! Hejdå!'

    def _get_context(self, conversation_id):
        context = self.conversations_en[conversation_id].get_dialogue_history()
        return context


class InterviewConversation:

    def __init__(self, name, job, tokenizer):
        self.name = name
        self.job = job.lower()
        self.conversation_sv = BlenderConversation(lang='sv', tokenizer=tokenizer)
        self.conversation_en = BlenderConversation(lang='en', tokenizer=tokenizer)
        self.nbr_replies = 0
        self.last_input_is_question = False
        self.episode_done = False
        self.questions = [question.format(self.job) if format_this else question for (question, format_this) in
                          read_questions((Path(__file__).parent / 'interview_questions.txt'))]
        self.tokenizer = tokenizer
        self.persona = 'your new_persona: I work in human resources\nyour new_persona: I have worked at this company for five years'
        self.persona_length = len(self.tokenizer(self.persona)['input_ids'])

    def reset_conversation(self):
        self.conversation_sv.reset()
        self.conversation_en.reset()
        return

    def get_context(self):
        context = '{}\n{}'.format(self.persona, self.conversation_en.get_dialogue_history())
        return context

    def fun2(self):
        raise NotImplementedError


class InterviewWorld(ChatWorld):
    # Class that keeps
    def __init__(self, **kwargs):
        # TODO: More sophisticated questions/greeting drawn from txt file(?) and formated with name and job
        super().__init__(**kwargs)

        self.interviews = {}
        self.max_replies = 2  # Maximum number of replies back and forth for each question

    def init_conversation(self, conversation_id, name, job):
        """Creates a new empty conversation if the conversation id doesn't already exist"""
        # TODO: Better greetings
        greeting = 'Hej, {}! Välkommen till din intervju! Hur är det med dig?'.format(name)
        if conversation_id in self.interviews:
            self.interviews[conversation_id].reset_conversation()
            return greeting
        else:
            self.interviews[conversation_id] = InterviewConversation(
                name=name,
                job=job,
                tokenizer=self.tokenizer
            )
            return greeting

    def observe(self, user_input, conversation_id):
        # TODO: Is question? We don't want to reply to a question with a question. if is_question: reply model_answer + interview_question
        # TODO: Better check of input stop
        # Observe the user input, translate and update internal states.
        # Returns boolean indicating if interview episode is done
        # We assume the user_input is always grammatically correct!

        interview = self.interviews[conversation_id]
        if '?' in user_input:
            interview.last_input_is_question = True

        translated_input = self.translator.translate(user_input, src='sv', target='en')
        interview.conversation_sv.add_user_text(user_input)
        interview.conversation_en.add_user_text(translated_input)

        # Set episode done if exit condition is met.
        if interview.nbr_replies == self.max_replies and len(
                interview.questions) == 0 \
                or user_input.lower().replace(' ', '') in self.stop_tokens:
            interview.episode_done = True

        return interview.episode_done

    def act(self, conversation_id):
        """There are four cases we can encounter that we treat differently:
         1. No more interview questions         --> End conversation
         2. Model has chatted freely for a bit  --> Force next interview questions
         3. Same as last, but user has just written a question --> return reply + new question
         4. Model is allowed to chat more
           Code is slightly messy so the four cases are marked with 'Case X' in the code """
        # If it's time for another interview question, we don't need to pass anything through the mode
        interview = self.interviews[conversation_id]

        if interview.episode_done:
            # Case 1
            # interview.save()
            interview.reset_conversation()
            bye = 'Tack för din tid, det var trevligt att få intervjua dig!'
            return bye
        elif interview.nbr_replies == self.max_replies and not interview.last_input_is_question:
            # Case 2
            interview.nbr_replies = 0
            interview_question = interview.questions.pop(0)
            interview_question_en = self.translator.translate(interview_question, src='sv', target='en')
            interview.conversation_sv.add_bot_text(interview_question)
            interview.conversation_en.add_bot_text(interview_question_en)
            return interview_question
        else:
            context = interview.get_context()
            inputs = self.tokenizer([context], return_tensors='pt')
            inputs.to(self.device)
            with no_grad():
                output_tokens = self.model.generate(**inputs)
                reply_en = self.tokenizer.decode(output_tokens[0], skip_special_tokens=True)

            reply_en = self._correct_reply(reply_en, conversation_id)
            # _correct_reply can return empty string -> force new question
            if len(reply_en) < 3:
                interview.nbr_replies = 0
                try:
                    reply_sv = interview.questions.pop(0)
                    reply_en = self.translator.translate(reply_sv, src='sv', target='en')
                except IndexError:
                    reply_en = 'Thank you for your time. We will keep in touch'
                    reply_sv = 'Tack för din tid, det var trevligt att få intervjua dig!'
                    interview.episode_done = True
            elif interview.nbr_replies == self.max_replies and interview.last_input_is_question:
                # Case 3 - Add new question to end of model reply
                reply_sv = self.translator.translate(reply_en, src='en', target='sv') + ' ' + interview.questions.pop(0)
                reply_en = self.translator.translate(reply_sv, src='sv', target='en')
                interview.nbr_replies = 0
            else:
                # Case 4
                interview.nbr_replies += 1
                reply_sv = self.translator.translate(reply_en, src='en', target='sv')
            interview.conversation_sv.add_bot_text(reply_sv)
            interview.conversation_en.add_bot_text(reply_en)
            return reply_sv

    def _correct_reply(self, reply, conversation_id):
        # For every bot reply, check what sentences are repetitive and remove that part only.
        # Current check will discard a sentence where she asks something new but with a little detail
        interview = self.interviews[conversation_id]
        previous_replies = interview.conversation_en.get_bot_replies()

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

        # Emely cannot say that she's also a {job}, or that she 'jobbar i timme'
        lies = ['I am a {}'.format(interview.job),
                'I work for an hour']
        temp_idx = []
        for i in keep_idx:
            for lie in lies:
                lie_prob = SequenceMatcher(a=lie, b=sentences[i]).ratio()
                if lie_prob < 0.75:
                    temp_idx.append(i)
                else:
                    logging.warning('Identified lie removed: {}'.format(lie))
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
