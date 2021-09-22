from dataclasses import dataclass, asdict
from pathlib import Path
import random
from src.chat.questions import QuestionGenerator
from typing import List, Optional

""" File contents:
- Firestore objects used for storing data in the database
- Conversation objects: Classes used for handling a fika or interview conversation

The FirestoreConversation object is basically a data representation of the 
FikaConversation/InterviewConversation objects.
"""


@dataclass
class FirestoreMessage(object):
    """ Dataclass used to push Message data to the Firestore database """
    conversation_id: str    # Unique ID assigned by firestore
    msg_nbr: int            # Starts at 0
    who: str                # 'user' or 'bot'
    created_at: str         # Timestamp
    response_time: float    #
    lang: str               # Language: 'sv'
    message: str            # Message in lang
    message_en: str         # Message in english
    case_type: str          # Case in worlds.act()
    recording_used: bool    # Whether the STT-recording was used or not
    removed_from_message: str       # Message that was removed using world._correct_reply
    is_more_information: bool       # Specific type of hardcoded message
    is_init_message: bool           # Specific type of hardcoded message
    is_predefined_question: bool    # Specific type of hardcoded message
    is_hardcoded: bool      #
    error_messages: str     #
    message_rating: int = 0  # Used for feedback in webapp, possibly reinforcement learning later on

    @staticmethod
    def from_dict(source):
        return FirestoreMessage(**source)

    def to_dict(self):
        return asdict(self)


@dataclass
class FirestoreConversation(object):
    """ Dataclass used to push Conversation data to the Firestore database """
    # Fixed attributes
    name: str  # Name
    persona: str  # Emelys persona
    created_at: str  # Timestamp
    lang: str  # Language
    development_testing: bool  # If conversation is an internal test
    webapp_local: bool  # Locally run webapp
    webapp_url: str  # Client host of webapp
    webapp_version: str  #
    user_ip_number: str  #
    brain_url: str  # Client host of brain
    brain_version: str  #

    # Updated attributes - Used in Fika/InterviewConversation
    interview_questions: Optional[List] = None
    episode_done: bool = False  # Is the conversation over?
    nbr_messages: int = 0  #
    last_input_is_question: bool = False  # Was the last user input a question?
    model_replies_since_last_question: int = 0  # Used to steer Emely
    pmrr_more_information: str = '012'  # TODO: Fix predefined list

    job: str = None  # Only used for interview, not fika


    @staticmethod
    def from_dict(source):
        return FirestoreConversation(**source)

    def to_dict(self):
        return asdict(self)

@dataclass
class BadwordMessage(object):
    message: str
    conversation_id: str
    created_at: str
    development_testing: str

    @staticmethod
    def from_dict(source):
        return OffensiveMessage(**source)

    def to_dict(self):
        return asdict(self)


# TODO: Write superclasss
# class Conversation:
#     """Super class """
#     def __init__(self):
#
#
#     def add_text(self, firestore_message: FirestoreMessage):
#         """ Pushes new message to database
#         """
#         self.nbr_messages += 1
#         msg_nbr = firestore_message.msg_nbr
#         assert msg_nbr == self.nbr_messages - 1, 'Whoopsie daisy: msg nbr in message and total nbr_messages in conversation do not match'
#
#         doc_ref = self.firestore_messages_collection.document(str(msg_nbr))  #
#         doc_ref.set(firestore_message.to_dict())
#         return


class FikaConversation:
    """ Class that tracks the states of a conversation with fika Emely.
    Is initialised with a FirestoreConversation object"""

    def __init__(self, firestore_conversation: FirestoreConversation, conversation_id,
                 firestore_conversation_collection):
        self.firestore_conversation = firestore_conversation
        self.name = firestore_conversation.name
        self.conversation_id = conversation_id
        self.lang = firestore_conversation.lang

        # Attributes to update
        self.episode_done = firestore_conversation.episode_done
        self.nbr_messages = firestore_conversation.nbr_messages
        self.last_input_is_question = firestore_conversation.last_input_is_question
        self.model_replies_since_last_question = firestore_conversation.model_replies_since_last_question

        # Fika specific - draw from db or file # TODO:
        # self.pmrr_more_information = [c for c in
        # firestore_conversation.pmrr_more_information]  # Split '1234 into ['1','2','3','4']
        self.change_subject = ['Berätta något annat om dig själv!',
                               'Nu tycker jag att vi ska prata om något annat!',
                               'Vill du prata om något annat kanske?',
                               'Får jag föreslå att vi hittar något annat att prata om?',
                               'Nog om det. Vad händer i ditt liv annars?',
                               'Äsch, vi pratar om något annat. Har det hänt något roligt på sistone?',
                               'Jag skulle vilja att vi pratar om något annat.',
                               'Det känns som att vi inte kommer längre i denna diskussion. Hur är läget annars?']

        # Firestore
        self.firestore_messages_collection = firestore_conversation_collection.document(conversation_id).collection(
            'messages')
        self.firestore_conversation_ref = firestore_conversation_collection.document(conversation_id)

        # Not used currently
        self.persona = ''
        self.persona_length = 0  # len(self.tokenizer(self.persona)['input_ids'])

    # TODO: Move to superclass
    def add_text(self, firestore_message: FirestoreMessage):
        """ Adds a message to the conversation by pushing it to firestore """
        self.nbr_messages += 1
        msg_nbr = firestore_message.msg_nbr
        assert msg_nbr + 1 == self.nbr_messages, 'Whoopsie daisy: msg nbr in message and total nbr_messages in conversation do not match'

        doc_ref = self.firestore_messages_collection.document(str(msg_nbr))
        doc_ref.set(firestore_message.to_dict())
        return

    def get_next_hardcoded_message(self):
        """ Returns the next hardcoded message that tries to change the subject of the conversation """
        utterance = random.choice(self.change_subject)
        return utterance

    def get_input_with_context(self):
        """ Returns the input for the model, which currently is the last four messages of the conversation """
        nbr_replies_for_context = 20
        condition = self.nbr_messages - nbr_replies_for_context - 1
        docs = self.firestore_messages_collection.where('msg_nbr', '>=', condition).stream()
        messages = [doc.to_dict() for doc in docs]
        messages.sort(key=lambda x: x['msg_nbr'])
        context = ''
        for i, message in enumerate(messages):
            if i == len(messages) - 1:  #
                context = context + message['message_en']
            else:
                context = context + message['message_en'] + '\n'

        return context

    def _update_fire_object(self):
        """ Helper function: Updates the attributes of the FirestoreConversation object """
        self.firestore_conversation.episode_done = self.episode_done
        self.firestore_conversation.nbr_messages = self.nbr_messages
        self.firestore_conversation.last_input_is_question = self.last_input_is_question
        self.firestore_conversation.model_replies_since_last_question = self.model_replies_since_last_question
        return

    # TODO: MOve to superclass
    def get_bot_replies(self):
        """ Retrieves all previous bot messages in the conversation and returns them as a list.
            Is used for _correct_reply in worlds.py """
        docs = self.firestore_messages_collection.where('who', '==', 'bot').stream()
        messages = [doc.to_dict() for doc in docs]
        messages.sort(key=lambda x: x['msg_nbr'])
        replies = [m['message_en'] for m in messages]
        return replies

    # TODO: Move to superclass(does it work despite unique update_fire_object fucntions?)
    def push_to_firestore(self):
        """ Pushes the updated FirestoreConversation to the firestore database at the end of act() in worlds.py """
        self._update_fire_object()
        self.firestore_conversation_ref.set(self.firestore_conversation.to_dict())
        return


class InterviewConversation:
    """ Class that tracks the states of a conversation with intervju Emely.
        Is initialised with a FirestoreConversation object. """

    def __init__(self, firestore_conversation: FirestoreConversation, conversation_id,
                 firestore_conversation_collection):
        self.firestore_conversation = firestore_conversation
        self.name = firestore_conversation.name
        self.job = firestore_conversation.job
        self.conversation_id = conversation_id
        self.lang = firestore_conversation.lang

        # Attributes to update
        self.episode_done = firestore_conversation.episode_done
        self.nbr_messages = firestore_conversation.nbr_messages
        self.last_input_is_question = firestore_conversation.last_input_is_question
        self.model_replies_since_last_question = firestore_conversation.model_replies_since_last_question

        # Retrieves hard coded messages
        self.interview_questions = [c for c in firestore_conversation.interview_questions]  
        self.pmrr_more_information = [c for c in firestore_conversation.pmrr_more_information]

        self.more_information = None
        #self._get_interview_questions()
        self._get_more_information()

        # Firestore
        self.firestore_messages_collection = firestore_conversation_collection.document(conversation_id).collection(
            'messages')
        self.firestore_conversation_ref = firestore_conversation_collection.document(conversation_id)

        # Not used currently
        self.persona = ''
        self.persona_length = 0  # len(self.tokenizer(self.persona)['input_ids'])

    # TODO: Move to superclass
    def add_text(self, firestore_message: FirestoreMessage):
        """ Adds a message to the conversation by pushing it to firestore """
        self.nbr_messages += 1
        msg_nbr = firestore_message.msg_nbr
        assert msg_nbr + 1 == self.nbr_messages, 'Whoopsie daisy: msg nbr in message and total nbr_messages in conversation do not match'

        doc_ref = self.firestore_messages_collection.document(str(msg_nbr))
        doc_ref.set(firestore_message.to_dict())
        return

    def _get_interview_questions(self):
        """ Gets interview quesitons from QuestionGenerator. Formatted with competences for 17 different jobs
        """
        q = QuestionGenerator()
        job = self.job.strip(' ')

        return q.get_interview_questions(job)

    # TODO: Retrieve more information from database instead of from file
    def _get_more_information(self):
        """ Helper function: Reads more information utterances from file.
        """
        more_info_path = Path(__file__).resolve().parent.joinpath('more_information.txt')
        with open(more_info_path, 'r') as f:
            text = f.read()
        self.more_information = text.split('\n')
        return

    def get_next_interview_question(self):
        """Pops the next question from the interview_questions list
           and returns the corresponding question """
        try:
            question = self.interview_questions.pop(0)
            self.model_replies_since_last_question = 0
        except Exception as e:
            print(e)
            self.episode_done = True
            return 'Oj jag måste tyvärr avsluta intervjun lite tidigt men tack för din tid!'
        return question

    def get_next_more_information(self):
        """Pops a more information message"""
        try:
            index = int(self.pmrr_more_information.pop())
            more_info = self.more_information[index]
            contains_question = False
        except IndexError:
            more_info = 'Jag tycker att vi går vidare. ' + self.get_next_interview_question()
            contains_question = True
        return more_info, contains_question

    def get_input_with_context(self):
        """ Creates input for model: the conversation history since the last predefined question! """
        #nbr_replies_for_context = 2 + self.model_replies_since_last_question * 2 + 2
        nbr_replies_for_context = 10
        condition = self.nbr_messages - nbr_replies_for_context
        docs = self.firestore_messages_collection.where('msg_nbr', '>=', condition).stream()
        messages = [doc.to_dict() for doc in docs]
        messages.sort(key=lambda x: x['msg_nbr'])
        context = ''
        for i, message in enumerate(messages):
            if i == len(messages) - 1:  # We don't want a '\n' after the last line
                context = context + message['message_en']
            else:
                context = context + message['message_en'] + '\n'

        return context

    # TODO: MOve to superclass
    def get_bot_replies(self):
        """ Retrieves all previous bot messages in the conversation and returns them as a list.
            Is used for _correct_reply in worlds.py """
        docs = self.firestore_messages_collection.where('who', '==', 'bot').stream()
        messages = [doc.to_dict() for doc in docs]
        messages.sort(key=lambda x: x['msg_nbr'])
        replies = [m['message_en'] for m in messages]
        return replies

    def _update_fire_object(self):
        """ Helper function: Updates the attributes of the FirestoreConversation object """
        self.firestore_conversation.episode_done = self.episode_done
        self.firestore_conversation.nbr_messages = self.nbr_messages
        self.firestore_conversation.last_input_is_question = self.last_input_is_question
        self.firestore_conversation.model_replies_since_last_question = self.model_replies_since_last_question
        self.firestore_conversation.interview_questions = self.interview_questions

        pmrr_information = ''
        for c in self.pmrr_more_information:
            pmrr_information = pmrr_information + c
        self.firestore_conversation.pmrr_more_information = pmrr_information

        return

    # TODO: Move to superclass(does it work despite unique update_fire_object fucntions?)
    def push_to_firestore(self):
        """ Pushes the updated FirestoreConversation to the firestore database at the end of act() in worlds.py """
        self._update_fire_object()
        self.firestore_conversation_ref.set(self.firestore_conversation.to_dict())
        return
