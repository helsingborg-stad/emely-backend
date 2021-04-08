from transformers import BlenderbotTokenizer, BlenderbotForConditionalGeneration, BlenderbotSmallTokenizer, \
    BlenderbotSmallForConditionalGeneration
from torch import no_grad
import torch

import re
from itertools import product
from difflib import SequenceMatcher
import random

from pathlib import Path

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from src.chat.conversation import FikaConversation, InterviewConversation, FirestoreConversation, FirestoreMessage
from src.chat.translate import ChatTranslator
from src.api.utils import is_gcp_instance
from src.api.bodys import BrainMessage, UserMessage, InitBody
from src.chat.utils import user_message_to_firestore_message, firestore_message_to_brain_message
from datetime import datetime


class ChatWorld:

    def __init__(self, **kwargs):
        # Attributes common for both ChatWorld and InterviewWorld
        self.model_name = kwargs['model_name']
        self.local_model = kwargs['local_model']
        self.no_correction = kwargs['no_correction']
        # TODO: deprecate device, model, but not tokenizer!
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.tokenizer = None
        self.model_loaded = False

        if is_gcp_instance():
            if not firebase_admin._apps:
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred, {
                    'projectId': 'emelybrainapi',
                })

            self.firestore_client = firestore.client()
        else:
            # Use a service account
            if not firebase_admin._apps:
                json_path = Path(__file__).resolve().parents[2].joinpath('emelybrainapi-33194bec3069.json')
                cred = credentials.Certificate(json_path.as_posix())
                firebase_admin.initialize_app(cred)

            self.firestore_client = firestore.client()

        # Message collection will depend on the conversation
        self.firestore_conversation_collection = self.firestore_client.collection('conversations')

        self.translator = ChatTranslator()

        self.stop_tokens = ['hejdå', 'bye', 'hej då']
        self.greetings = ['Hej {}, jag heter Emely! Hur är det med dig?',
                          'Hej {}! Mitt namn är Emely. Vad vill du prata om idag?',
                          'Hejsan! Jag förstår att du heter {}. Berätta något om dig själv!']

    # TODO: Deprecate function after deploying models to gcp!
    def load_model(self):
        """Loads model from huggingface or locally. Works with both BlenderbotSmall and regular"""
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

    def init_conversation(self, init_body: InitBody):
        """Creates a new empty conversation if the conversation id doesn't already exist"""

        # Creates a greeting message
        name = init_body.name.capitalize()
        greeting = random.choice(self.greetings).format(name)
        greeting_en = 'Hi {}, my name is Emely. How are you today?'.format(name)

        # Convert to dict and remove data not needed
        init_body = init_body.dict()
        init_body.pop('password')

        # Create FirestoreConversation, push to db and get conversation_id
        fire_convo = FirestoreConversation.from_dict(init_body)
        print('Is all the information needed for firestoreconversation in init_body?')  # TODO:Check
        conversation_ref = self.firestore_conversation_collection.document()
        conversation_ref.set(fire_convo.to_dict())
        conversation_id = conversation_ref.id
        print('Conversation id is: ', conversation_id)

        # Time
        webapp_creation_time = datetime.fromisoformat(init_body['created_at'])
        init_timestamp = datetime.now()
        response_time = str(init_timestamp - webapp_creation_time)

        # Create FirestoreMessage
        fire_msg = FirestoreMessage(conversation_id=conversation_id,
                                    msg_nbr=0, who='bot', created_at=str(init_timestamp), response_time=response_time,
                                    lang=fire_convo.lang, message=greeting, message_en=greeting_en, case_type='None',
                                    recording_used=False, removed_from_message='', is_more_information=False,
                                    is_init_message=True, is_predefined_question=False, is_hardcoded=True,
                                    error_messages='')

        # Create a FikaConversation
        new_conversation = FikaConversation(firestore_conversation=fire_convo, conversation_id=conversation_id,
                                            firestore_conversation_collection=self.firestore_conversation_collection)
        new_conversation.add_text(fire_msg)

        # Get updated firestoreconversation and update it in database by overwriting
        fire_convo = new_conversation.get_fire_object()
        conversation_ref.set(fire_convo.to_dict())

        response = BrainMessage(conversation_id=conversation_id,
                                lang=init_body['lang'],
                                message=greeting,
                                is_init_message=True,
                                is_hardcoded=True,
                                error_messages='None')

        return response

    def observe(self, user_request: UserMessage):
        # Observe the user input, translate and update internal states
        # Check if user wants to quit/no questions left --> self.episode_done = True
        observe_timestamp = datetime.now()

        # Extract information and translate message
        conversation_id = user_request.conversation_id
        message = user_request.message
        message_en = self.translator.translate(message, src='sv', target='en')

        # Create conversation from firestore data
        fire_convo = self._get_fire_conversation(conversation_id)
        conversation = FikaConversation(firestore_conversation=fire_convo, conversation_id=conversation_id,
                                        firestore_conversation_collection=self.firestore_conversation_collection)

        # Convert user message to firestore message and add it to conversation
        firestore_message = user_message_to_firestore_message(user_message=user_request,
                                                              translated_message=message_en,
                                                              msg_nbr=conversation.nbr_messages)
        conversation.add_text(firestore_message)

        # Set episode done if exit condition is met.
        if message.lower().replace(' ', '') in self.stop_tokens:
            conversation.episode_done = True
        return conversation, observe_timestamp

    def act(self, conversation: FikaConversation, observe_timestamp):
        if not conversation.episode_done:
            # Preparation for model
            context = conversation.get_input_with_context()
            inputs = self.tokenizer([context], return_tensors='pt')  # TODO: Replace with call to model on gcp funciton
            inputs.to(self.device)
            with no_grad():
                output_tokens = self.model.generate(**inputs)
            reply_en = self.tokenizer.decode(output_tokens[0], skip_special_tokens=True)

            if self.no_correction:  # Reply isn't checked/modified in any way. Used for testing purposes
                reply_sv = self.translator.translate(reply_en, src='en', target='sv')
                removed_from_message = ''
                case = 'no_correction'
                is_hardcoded = False
            else:  # Removes repetitive statements
                reply_en, removed_from_message = self._correct_reply(reply_en, conversation)
                if len(reply_en) < 3:  # TODO: Move the popping and length check into correct reply
                    removed_from_message = ''  # We're forcing a new hardcode anyway
                    case = 'hardcode'
                    is_hardcoded = True
                    try:
                        reply_sv = conversation.get_next_hardcoded_message()
                        reply_en = self.translator.translate(reply_sv, src='sv', target='en')
                    except IndexError:
                        conversation.episode_done = True
                        return 'Nu måste jag gå. Det var kul att prata med dig! Hejdå!'
                else:
                    reply_sv = self.translator.translate(reply_en, src='en', target='sv')
                    case = 'correction'
                    is_hardcoded = False

            # Create FirestoreMessage
            act_timestamp = datetime.now()
            response_time = str(act_timestamp - observe_timestamp)
            firestore_message = FirestoreMessage(conversation_id=conversation.conversation_id,
                                                 msg_nbr=conversation.nbr_messages, who='bot',
                                                 created_at=str(act_timestamp),
                                                 response_time=response_time,
                                                 lang=conversation.lang, message=reply_sv,
                                                 message_en=reply_en,
                                                 case_type=case,
                                                 recording_used=False, removed_from_message=removed_from_message,
                                                 is_more_information=False,
                                                 is_init_message=False, is_predefined_question=False,
                                                 is_hardcoded=is_hardcoded,
                                                 error_messages='')
            conversation.add_text(firestore_message)

            # Create BrainMessage
            brain_response = firestore_message_to_brain_message(firestore_message)

            # Get firestore object and push to database
            fire_conversation = conversation.get_fire_object()
            conversation_ref = self.firestore_conversation_collection.document(conversation.conversation_id)
            conversation_ref.set(fire_conversation.to_dict())

            return brain_response

        else:  # Episode is done
            # Time
            act_timestamp = datetime.now()
            response_time = str(act_timestamp - observe_timestamp)

            # Message
            bye_sv = 'Nu måste jag gå. Det var kul att prata med dig! Hejdå!'
            bye_en = 'I have to leave now. Bye!'

            # Get firestore and push to database
            firestore_message = FirestoreMessage(conversation_id=conversation.conversation_id,
                                        msg_nbr=conversation.nbr_messages, who='bot',
                                        created_at=str(act_timestamp),
                                        response_time=response_time,
                                        lang=conversation.lang, message=bye_sv,
                                        message_en=bye_en,
                                        case_type='episode_done',
                                        recording_used=False, removed_from_message='',
                                        is_more_information=False,
                                        is_init_message=False, is_predefined_question=False,
                                        is_hardcoded=True,
                                        error_messages='')
            conversation.add_text(firestore_message)
            brain_response = firestore_message_to_brain_message(firestore_message)

            fire_conversation = conversation.get_fire_object()
            conversation_ref = self.firestore_conversation_collection.document(conversation.conversation_id)
            conversation_ref.set(fire_conversation.to_dict())

            return brain_response

    # TODO: Create superclass function which can be called with some parameters specific for fika/interview?
    def _correct_reply(self, reply, conversation):
        # For every bot reply, check what sentences are repetitive and remove that part only.
        # Current check will discard a sentence where she asks something new but with a little detail

        previous_replies = conversation.get_bot_replies()

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
            if max(ratios) < 0.75:
                keep_idx.append(i)

        # Emely cannot say that she's also a {job}, add
        lies = ['I am Emely',
                'My name is Emely']
        temp_idx = []
        for i in keep_idx:
            combos = list(product([sentences[i]], lies))
            lie_probabilities = [SequenceMatcher(a=s1, b=s2).ratio() for s1, s2 in combos]
            if max(lie_probabilities) < 0.65:
                temp_idx.append(i)

        keep_idx = temp_idx

        if len(keep_idx) == len(sentences):  # Everything is fresh and we return it unmodified
            return reply, ''
        else:
            new_reply = ''  # Reply without repetitions
            removed_from_message = ''  # What we remove
            for i in range(len(sentences)):
                if i in keep_idx:
                    try:
                        new_reply = new_reply + sentences[i] + separators[i] + ' '
                    except IndexError:
                        new_reply = new_reply + sentences[i]
                else:
                    removed_from_message = removed_from_message + sentences[i] + ' '

            return new_reply, removed_from_message

    # TODO: Move to super
    def _get_fire_conversation(self, conversation_id):
        conversation_ref = self.firestore_conversation_collection.document(conversation_id)
        doc = conversation_ref.get()
        fire_conversation = FirestoreConversation.from_dict(doc.to_dict())
        return fire_conversation


class InterviewWorld(ChatWorld):
    # Class that keeps
    def __init__(self, **kwargs):
        # TODO: More sophisticated questions/greeting drawn from txt file(?) and formated with name and job
        super().__init__(**kwargs)
        self.max_replies = 2  # Maximum number of replies back and forth for each question
        self.greetings = ['Hej, {}! Välkommen till din intervju! Hur är det med dig?',
                          'Hej {}, Emely heter jag och det är jag som ska intervjua dig. Hur är det med dig idag?',
                          'Välkommen till din intervju {}! Jag heter Emely. Hur mår du idag?'
                          ]
        # TODO: Attribute for brain api
        # self.brain_api = pointer_to_gcp_

        # TODO: Set this locally in observe and act
        self.firestore_message_collection = None

    def init_conversation(self, conversation_id, name, **kwargs):
        """Creates a new empty conversation if the conversation id doesn't already exist"""
        job = kwargs['job']
        name = name.capitalize()
        greeting = random.choice(self.greetings).format(name)
        greeting_en = 'Hello, {}! Welcome to your interview! How are you?'.format(name)

        # Create new fire object
        interview_fire = InterviewFirestore(conversation_id=conversation_id, name=name, job=job)
        new_interview = InterviewConversation(fire=interview_fire, tokenizer=self.tokenizer)
        new_interview.conversation_en.add_bot_text(greeting_en)
        new_interview.conversation_sv.add_bot_text(greeting)

        # Get updated fire object and push it to firestore_client
        interview_fire = new_interview.get_fire_object()
        doc_ref = self.db.document(str(conversation_id))
        doc_ref.set(interview_fire.to_dict())

        return greeting

    def observe(self, user_input, conversation_id):
        # Observe the user input, translate and update internal states.
        # Returns boolean indicating if interview episode is done
        # We assume the user_input is always grammatically correct!

        doc = self.db.document(str(conversation_id)).get()
        fire_interview = InterviewFirestore.from_dict(doc.to_dict())

        interview = InterviewConversation(fire=fire_interview, tokenizer=self.tokenizer)

        if '?' in user_input:
            interview.last_input_is_question = True
        else:
            interview.last_input_is_question = False

        translated_input = self.translator.translate(user_input, src='sv', target='en')
        interview.conversation_sv.add_user_text(user_input)
        interview.conversation_en.add_user_text(translated_input)

        # Set episode done if exit condition is met.
        if interview.nbr_replies == self.max_replies and len(
                interview.questions) == 0 \
                or user_input.lower().replace(' ', '') in self.stop_tokens:
            interview.episode_done = True

        return interview.episode_done, interview

    def act(self, interview):
        """There are four cases we can encounter that we treat differently:
         1. No more interview questions         --> End conversation
         2. Model has chatted freely for a bit  --> Force next interview questions
         3. Same as last, but user has just written a question --> return reply + new question
         4. Model is allowed to chat more
           Code is slightly messy so the four cases are marked with 'Case X' in the code """
        # If it's time for another interview question, we don't need to pass anything through the mode

        if interview.episode_done:
            # Case 1
            # interview.save()
            self.db.document(str(interview.conversation_id)).delete()
            bye = 'Tack för din tid, det var trevligt att få intervjua dig!'
            return bye
        elif interview.nbr_replies == self.max_replies and not interview.last_input_is_question:
            # Case 2
            interview.nbr_replies = 0
            interview_question = interview.questions.pop(0)
            interview_question_en = self.translator.translate(interview_question, src='sv', target='en')
            interview.conversation_sv.add_bot_text(interview_question)
            interview.conversation_en.add_bot_text(interview_question_en)

            # Update firestore_client
            interview_fire = interview.get_fire_object()
            doc_ref = self.db.document(str(interview.conversation_id))
            doc_ref.set(interview_fire.to_dict())
            return interview_question
        else:
            context = interview.get_context()

            # TODO: Call model from other gcp function
            inputs = self.tokenizer([context], return_tensors='pt')
            inputs.to(self.device)

            with no_grad():
                output_tokens = self.model.generate(**inputs)
                reply_en = self.tokenizer.decode(output_tokens[0], skip_special_tokens=True)
            # TODO: end

            if self.no_correction:
                pass
            else:
                reply_en = self._correct_reply(reply_en, interview)
            # _correct_reply can return empty string -> force 'more info reply' (commented force new question)
            if len(reply_en) < 3:
                # interview.nbr_replies = 0
                # reply_sv = interview.questions.pop(0)
                if len(interview.questions) == 5:
                    reply_sv = interview.questions.pop(0)
                    reply_en = self.translator.translate(reply_sv, src='sv', target='en')
                    interview.nbr_replies = 0
                else:
                    try:
                        reply_sv = interview.more_information.pop()
                    except IndexError:
                        reply_sv = 'Jag förstår. Kan du berätta lite mer om det?'
                    reply_en = self.translator.translate(reply_sv, src='sv', target='en')
                    interview.nbr_replies += 1
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

            # Update firestore_client
            interview_fire = interview.get_fire_object()
            doc_ref = self.db.document(str(interview.conversation_id))
            doc_ref.set(interview_fire.to_dict())
            return reply_sv

    # TODO: Implement returning removed from message
    def _correct_reply(self, reply, conversation):
        # For every bot reply, check what sentences are repetitive and remove that part only.
        # Current check will discard a sentence where she asks something new but with a little detail
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

        # Emely cannot say that she's also a {job}, add
        lies = ['I am a {}'.format(interview.job),
                'do you have any hobbies?']
        temp_idx = []
        for i in keep_idx:
            combos = list(product([sentences[i]], lies))
            lie_probabilities = [SequenceMatcher(a=s1, b=s2).ratio() for s1, s2 in combos]
            if max(lie_probabilities) < 0.75:
                temp_idx.append(i)

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

            return new_reply

    # TODO: Move to super
    def _get_fire_conversation(self, conversation_id):
        conversation_ref = self.firestore_conversation_collection.document(conversation_id)
        doc = conversation_ref.get()
        fire_conversation = FirestoreConversation.from_dict(doc.to_dict())
        return fire_conversation
