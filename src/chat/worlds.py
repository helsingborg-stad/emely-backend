from googletrans import Translator
from transformers import BlenderbotTokenizer, BlenderbotForConditionalGeneration
from torch import no_grad
import torch
import random
from conversation import BlenderConversation
import re
from itertools import product
from difflib import SequenceMatcher


class ChatWorld:
    # Class that keeps

    def __init__(self, mname='facebook/blenderbot-400M-distill'):
        # TODO: init model and tokenizer from file
        # TODO: init from opt like dictionary

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = BlenderbotForConditionalGeneration.from_pretrained(mname)
        self.model.to(self.device)
        self.tokenizer = BlenderbotTokenizer.from_pretrained(mname)

        self.model_name = mname.replace('facebook/', '')
        self.translator = Translator()
        self.episode_done = False
        self.stop_tokens = ['färdig', 'slut', 'hejdå', 'done']  # TODO: Snyggare lösning

        self.conversation_sv = BlenderConversation(lang='sv', tokenizer=self.tokenizer)
        self.conversation_en = BlenderConversation(lang='en', tokenizer=self.tokenizer)
        self.description = 'Open dialogue with {}'.format(self.model_name)

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

        # Set episode done if exit conidion is met. TODO: Better check of input stop
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
        out = self.translator.translate(text, src='sv', dest='en')
        if out.text == text:
            print('Input: {} \n Output: {}'.format(text, out.text))
            self.save(error='translation')
            raise ValueError('String not translated properly')
        return out.text

    def _en_to_sv(self, text):
        out = self.translator.translate(text, src='en', dest='sv')
        if out.text == text:
            print('Input: {} \n Output: {}'.format(text, out.text))
            self.save(error='translation')
            raise ValueError('String not translated properly')
        return out.text


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
        if self.nbr_replies == self.max_replies:
            self.nbr_replies = 0
            interview_question = self.questions.pop()
            interview_question_en = self._sv_to_en(interview_question)
            self.conversation_sv.add_bot_text(interview_question)
            self.conversation_en.add_bot_text(interview_question_en)
            return interview_question
        elif not self.episode_done:
            context = self._get_context()
            inputs = self.tokenizer([context], return_tensors='pt')
            inputs.to(self.device)
            with no_grad():
                output_tokens = self.model.generate(**inputs)
            reply = self.tokenizer.decode(output_tokens[0], skip_special_tokens=True)
            reply = self._correct_reply(reply)

            if reply == '':  # Correct reply can return empty string
                reply = self.questions.pop()
                self.nbr_replies = 0
            else:
                self.nbr_replies += 1

            translated_reply = self._en_to_sv(reply)
            print(translated_reply)
            self.conversation_sv.add_bot_text(translated_reply)
            self.conversation_en.add_bot_text(reply)
        else:
            self.save()
            print('Tack för din intervju')
        return

    def _get_context(self):
        # persona + dialogue history
        return self.persona + '\n' + self.conversation_en.get_dialogue_history(125 - self.persona_length)

    def _validate_reply(self, reply):
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

    # TODO: Implement another version
    def correct_reply(self, reply):
        # Overrides the previous
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

        # For each part/sentence of the new reply, save it if it's not close to something said before
        keep_idx = []
        for i in range(len(sentences)):
            combos = list(product([sentences[i]], previous_sentences))
            ratios = [SequenceMatcher(a=s1, b=s2).ratio() for s1, s2 in combos]
            if max(ratios) < 0.5:
                keep_idx.append(i)

        if len(keep_idx) == len(sentences):
            return reply
        else:
            new_reply = ''
            for i in keep_idx:
                try:
                    new_reply = new_reply + sentences[i] + separators[i] + ' '
                except IndexError:
                    new_reply = new_reply + sentences[i]
            return new_reply


def read_questions(file_path):
    # Reads interview questions from a text file, one question per line. '{}' in place where job should be inserted
    with open(file_path, 'r') as f:
        questions = f.readlines()
    format_this = [True if '{}' in question else False for question in questions]
    return zip(questions, format_this)
