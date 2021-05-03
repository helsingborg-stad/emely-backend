import requests
from src.api.bodys import ApiMessage

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
from src.chat.utils import user_message_to_firestore_message, firestore_message_to_brain_message, format_response_time
from datetime import datetime

import logging

""" File contents
 - FikaWorld: Handles fika conversation with Emely
 - InterviewWorld: Handles interview conversation with Emely 
 - TODO: ChatWorld - parent class
 
 The worlds all implement functions:
  - init_conversation: Creates new conversation, greets user and pushes data to firestore 
  - observe: observes new user input and updates internal states of conversation
  - act: acts upon the user_input together with the internal states
        - Generates text with model or
        - draw hardcoded reply from list
  - _correct_reply: corrects the text generated by model(e.g. removes repetitive statements)
"""


# TODO: Change name to FikaWorld and implement parent class FikaWorld
class FikaWorld:
    """ Handles Fika conversation"""

    def __init__(self, **kwargs):
        # Attributes common for both FikaWorld and InterviewWorld
        self.model_name = kwargs['model_name']
        self.local_model = kwargs['local_model']
        self.no_correction = kwargs['no_correction']
        self.on_gcp = is_gcp_instance()
        # TODO: deprecate device, model, but not tokenizer!
        self.tokenizer = None
        self.model_url = 'https://fika-model-ef5bmjer3q-ew.a.run.app/inference' if True else "http://127.0.0.1:7000/inference"

        if self.on_gcp:
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

    def call_model(self, context):
        """ Sends context to model and gets a reply back """
        context_json = ApiMessage(text=context).json()
        response = requests.post(url=self.model_url, data=context_json)
        json_response = response.json()
        reply = json_response['text']
        return reply

    def init_conversation(self, init_body: InitBody, build_data):
        """ Creates a new fika conversation that is pushed to firestore and replies with a greeting"""

        # Creates a greeting message
        name = init_body.name.capitalize()
        greeting = random.choice(self.greetings).format(name)
        greeting_en = 'Hi {}, my name is Emely. How are you today?'.format(name)

        # Convert initialization data to a dict and update with build data
        initial_information = init_body.dict()
        initial_information.update(build_data)
        initial_information.pop('password')  # Not needed

        # Create FirestoreConversation, push to db and get conversation_id
        fire_convo = FirestoreConversation.from_dict(initial_information)
        conversation_ref = self.firestore_conversation_collection.document()
        conversation_ref.set(fire_convo.to_dict())
        conversation_id = conversation_ref.id

        # Time
        webapp_creation_time = datetime.fromisoformat(initial_information['created_at'])
        init_timestamp = datetime.now()
        response_time = format_response_time(init_timestamp - webapp_creation_time)

        # Create FirestoreMessage
        fire_msg = FirestoreMessage(conversation_id=conversation_id,
                                    msg_nbr=0, who='bot', created_at=str(init_timestamp), response_time=response_time,
                                    lang=fire_convo.lang, message=greeting, message_en=greeting_en, case_type='init',
                                    recording_used=False, removed_from_message='', is_more_information=False,
                                    is_init_message=True, is_predefined_question=False, is_hardcoded=True,
                                    error_messages='')

        # Create a FikaConversation
        new_conversation = FikaConversation(firestore_conversation=fire_convo, conversation_id=conversation_id,
                                            firestore_conversation_collection=self.firestore_conversation_collection)
        new_conversation.add_text(fire_msg)

        # Update the firestore conversation and push it to firestore
        new_conversation.push_to_firestore()

        # Create response
        response = firestore_message_to_brain_message(fire_msg)

        return response

    def observe(self, user_request: UserMessage) -> (FikaConversation, datetime):
        """ Observes a UserMessage
          1. Pulls conversaton from firestore
          2. Adds message to conversation
          3. Returns conversation to use in act()
          """
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

    def act(self, conversation: FikaConversation, observe_timestamp: datetime) -> BrainMessage:
        """ Creates a response for the conversation """
        if not conversation.episode_done:
            # Request answer from model
            context = conversation.get_input_with_context()
            reply_en = self.call_model(context)

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
            response_time = format_response_time(act_timestamp - observe_timestamp)
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

            # Push to firestore
            conversation.push_to_firestore()

            return brain_response

        else:  # Episode is done
            # Time
            act_timestamp = datetime.now()
            response_time = format_response_time(act_timestamp - observe_timestamp)

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
        """ Corrects a reply from the blenderbot model.
            Removes any sentence that is similar to a sentence Emely has said previously """
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
        # For each part/sentence of the new reply, save it if it's similar to something said before
        for i in range(len(sentences)):
            combos = list(product([sentences[i]], previous_sentences))
            ratios = [SequenceMatcher(a=s1, b=s2).ratio() for s1, s2 in combos]
            if max(ratios) < 0.85:
                keep_idx.append(i)

        # Emely cannot say that she's also a {job}, add
        lies = ['I hate you']

        temp_idx = []
        for i in keep_idx:
            combos = list(product([sentences[i]], lies))
            lie_probabilities = [SequenceMatcher(a=s1, b=s2).ratio() for s1, s2 in combos]
            if max(lie_probabilities) < 0.9:
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
            logging.info('Pruned message. Removed sentence(s):\n{}\nCorrected reply:\n{}'.format(removed_from_message,
                                                                                                 new_reply))
            return new_reply, removed_from_message

    # TODO: Move to super
    def _get_fire_conversation(self, conversation_id):
        """ Helper function used to retrieve the firestore conversation corresponding to the conversation_id """
        conversation_ref = self.firestore_conversation_collection.document(conversation_id)
        doc = conversation_ref.get()
        fire_conversation = FirestoreConversation.from_dict(doc.to_dict())
        return fire_conversation


class InterviewWorld(FikaWorld):
    """ Handles interview conversations """

    def __init__(self, **kwargs):
        # TODO: More sophisticated questions/greeting drawn from txt file(?) and formated with name and job
        super().__init__(**kwargs)
        self.max_replies = 2  # Maximum number of replies back and forth for each question
        self.greetings = ['Hej, {}! Välkommen till din intervju! Hur är det med dig?',
                          'Hej {}, Emely heter jag och det är jag som ska intervjua dig. Hur är det med dig idag?',
                          'Välkommen till din intervju {}! Jag heter Emely. Hur mår du idag?'
                          ]
        self.question_markers = ['?', 'vad', 'hur', 'när', 'varför', 'vem']
        # TODO: Attribute for brain api
        self.model_url = 'https://interview8080-ef5bmjer3q-ew.a.run.app/inference' if True else "http://127.0.0.1:7000/inference"

    def init_conversation(self, init_body: InitBody, build_data):
        """ Creates a new interview conversation that is pushed to firestore and replies with a greeting"""

        # Creates greeting message
        job = init_body.job
        name = init_body.name.capitalize()
        greeting = random.choice(self.greetings).format(name)
        greeting_en = 'Hello, {}! Welcome to your interview! How are you?'.format(name)

        # Convert initialization data to a dict and update with build data
        initial_information = init_body.dict()
        initial_information.update(build_data)
        initial_information.pop('password')  # Not needed

        # Create FirestoreConversation, push to db and get conversation_id
        fire_convo = FirestoreConversation.from_dict(initial_information)
        conversation_ref = self.firestore_conversation_collection.document()
        conversation_ref.set(fire_convo.to_dict())
        conversation_id = conversation_ref.id

        # Time
        webapp_creation_time = datetime.fromisoformat(initial_information['created_at'])
        init_timestamp = datetime.now()
        response_time = format_response_time(init_timestamp - webapp_creation_time)

        # Create FirestoreMessage
        fire_msg = FirestoreMessage(conversation_id=conversation_id,
                                    msg_nbr=0, who='bot', created_at=str(init_timestamp), response_time=response_time,
                                    lang=fire_convo.lang, message=greeting, message_en=greeting_en, case_type='init',
                                    recording_used=False, removed_from_message='', is_more_information=False,
                                    is_init_message=True, is_predefined_question=False, is_hardcoded=True,
                                    error_messages='')

        # Create InterviewConversation
        new_conversation = InterviewConversation(firestore_conversation=fire_convo, conversation_id=conversation_id,
                                                 firestore_conversation_collection=self.firestore_conversation_collection)
        new_conversation.add_text(fire_msg)

        # Update the firestore conversation and push it to firestore
        new_conversation.push_to_firestore()

        # Create response
        response = firestore_message_to_brain_message(fire_msg)

        return response

    def observe(self, user_request: UserMessage):
        """ Observes a UserMessage
          1. Pulls conversaton from firestore
          2. Adds message to conversation
          3. Returns conversation to use in act()
        """
        observe_timestamp = datetime.now()

        # Extract information and translate message
        conversation_id = user_request.conversation_id
        message = user_request.message
        message_en = self.translator.translate(message, src='sv', target='en')

        # Create conversation from firestore data
        fire_convo = self._get_fire_conversation(conversation_id)
        interview = InterviewConversation(firestore_conversation=fire_convo, conversation_id=conversation_id,
                                          firestore_conversation_collection=self.firestore_conversation_collection)

        # Convert user message to firestore message
        firestore_message = user_message_to_firestore_message(user_message=user_request,
                                                              translated_message=message_en,
                                                              msg_nbr=interview.nbr_messages)

        # Update states
        interview.add_text(firestore_message)  # Updates nbr_messages

        if any(marker in message.lower() for marker in self.question_markers):
            interview.last_input_is_question = True
        else:
            interview.last_input_is_question = False

        # Set episode done if exit condition is met.
        if interview.model_replies_since_last_question == self.max_replies and len(
                interview.pmrr_interview_questions) == 0 \
                or message.lower().replace(' ', '') in self.stop_tokens:
            interview.episode_done = True

        return interview, observe_timestamp

    def act(self, interview: InterviewConversation, observe_timestamp):
        """There are four cases we can encounter that we treat differently:
         1. No more interview questions         --> End conversation
         2. Model has chatted freely for a bit  --> Force next interview questions
         3. Model generates a reply that is totally revoked by correct reply and it forces new question instead
         4. Model should force new question, but user has just written a question --> return reply + new question
         5. Model is allowed to chat more
           Code is slightly messy so the four cases are marked with 'Case X' in the code """

        if interview.episode_done:
            # Case 1 - No more interview questions --> End conversation
            case = '1'

            # Data for FireMessage
            is_hardcoded = True
            is_predefined_question = False
            is_more_information = False
            removed_from_message = ''

            reply_sv = 'Tack för din tid, det var trevligt att få intervjua dig!'
            reply_en = 'Thanks for your time, it was nice to interview you!'
        elif interview.model_replies_since_last_question == self.max_replies and not interview.last_input_is_question:
            # Case 2 - Model has chatted freely for a bit  --> Force next interview questions
            case = '2'

            # Data for FireMessage
            is_hardcoded = True
            is_predefined_question = True
            is_more_information = False
            removed_from_message = ''

            interview.model_replies_since_last_question = 0
            reply_sv = interview.get_next_interview_question()
            reply_en = self.translator.translate(reply_sv, src='sv', target='en')

        else:  # Case 3, 4 or 5 - Model acts

            # Model call
            context = interview.get_input_with_context()
            reply_en = self.call_model(context)

            if not self.no_correction or len(interview.pmrr_interview_questions) == 5:
                reply_en, removed_from_message = self._correct_reply(reply_en, interview)
            else:
                removed_from_message = ''

            # _correct_reply can return empty string -> force 'more info reply' (commented force new question)
            if len(reply_en) < 3:
                # Case 3 - Model generates a reply that is totally revoked by correct reply and it forces new question instead
                case = '3'
                # Data for FireMessage
                is_more_information = True
                is_hardcoded = True
                removed_from_message = ''

                # TODO: Handle the greeting stage - we don't want a more info reply in the beginning...
                reply_sv, contains_question = interview.get_next_more_information()
                reply_en = self.translator.translate(reply_sv, src='sv', target='en')

                if contains_question:
                    interview.model_replies_since_last_question = 0
                    is_predefined_question = True
                else:
                    interview.model_replies_since_last_question += 1
                    is_predefined_question = False

            elif interview.model_replies_since_last_question == self.max_replies and interview.last_input_is_question:
                # Case 4 - Add new question to end of model reply
                case = '4'

                # Data for FireMessage
                is_hardcoded = False
                is_predefined_question = True
                is_more_information = False

                reply_sv = self.translator.translate(reply_en, src='en',
                                                     target='sv') + ' ' + interview.get_next_interview_question()
                reply_en = self.translator.translate(reply_sv, src='sv', target='en')
                interview.model_replies_since_last_question = 0
            else:
                # Case 5 - Model is allowed to chat more
                case = '5'

                # Data for FireMessage
                is_hardcoded = False
                is_predefined_question = False
                is_more_information = False

                interview.model_replies_since_last_question += 1
                reply_sv = self.translator.translate(reply_en, src='en', target='sv')

        # Time
        act_timestamp = datetime.now()
        response_time = format_response_time(act_timestamp - observe_timestamp)

        # Create a firestoremessage and add it
        firestore_message = FirestoreMessage(conversation_id=interview.conversation_id,
                                             msg_nbr=interview.nbr_messages, who='bot',
                                             created_at=str(act_timestamp),
                                             response_time=response_time,
                                             lang=interview.lang, message=reply_sv,
                                             message_en=reply_en,
                                             case_type=case,
                                             recording_used=False, removed_from_message=removed_from_message,
                                             is_more_information=is_more_information,
                                             is_init_message=False, is_predefined_question=is_predefined_question,
                                             is_hardcoded=is_hardcoded,
                                             error_messages='')
        brain_response = firestore_message_to_brain_message(firestore_message)
        interview.add_text(firestore_message)
        interview.push_to_firestore()

        return brain_response

    def _correct_reply(self, reply, conversation):
        """ Corrects a reply from the blenderbot model.
            - Removes any sentence that is similar to a sentence Emely has said previously.
            - Removes any sentences she's not allowed to say: e.g. I work as a __job__
        """
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
            if max(ratios) < 0.8:
                keep_idx.append(i)

        # Emely cannot say that she's also a {job}, add
        lies = ['I am a {}'.format(conversation.job),
                'do you have any hobbies?',
                "i'm a stay at home mom"]
        temp_idx = []
        for i in keep_idx:
            combos = list(product([sentences[i]], lies))
            lie_probabilities = [SequenceMatcher(a=s1, b=s2).ratio() for s1, s2 in combos]
            if max(lie_probabilities) < 0.9:
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

            logging.info('Pruned message. Removed sentence(s):\n{}\nCorrected reply:\n{}'.format(removed_from_message,
                                                                                                 new_reply))
            return new_reply, removed_from_message

    # TODO: Move to super
    def _get_fire_conversation(self, conversation_id):
        """ Helper function used to retrieve the firestore conversation corresponding to the conversation_id """
        conversation_ref = self.firestore_conversation_collection.document(conversation_id)
        doc = conversation_ref.get()
        fire_conversation = FirestoreConversation.from_dict(doc.to_dict())
        return fire_conversation
