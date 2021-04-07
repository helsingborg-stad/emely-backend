from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class FirestoreMessage(object):
    """ Dataclass used to push Message data to the Firestore database """
    conversation_id: str
    msg_nbr: int
    who: str
    created_at: datetime
    response_time: float
    lang: str
    message: str
    message_en: str
    case_type: str
    recording_used: bool  # Whether the STT-recording was used or not
    removed_from_message: str  # Message that was removed using world.correct_reply
    is_more_information: bool
    is_init_message: bool
    is_predefined_question: bool
    is_hardcoded: bool
    error_messages: str

    @staticmethod
    def from_dict(source):
        return FirestoreMessage(**source)

    def to_dict(self):
        return asdict(self)


@dataclass
class FirestoreConversation(object):
    """ Dataclass used to push Conversation data to the Firestore database """
    # Fixed attributes
    name: str
    persona: str
    job: str = None
    created_at: str = None
    development_testing: bool = None
    webapp_local: bool = None
    webapp_url: str = None
    webapp_version: str = None
    webapp_git_build: str = None
    brain_url: str = None
    brain_version: str = None
    brain_git_build: str = None
    user_ip_number: str = None
    lang: str = None

    # Updated attributes
    episode_done: bool = False
    nbr_messages: int = 0
    last_input_is_question: bool = False
    replies_since_last_question: int = -1
    pmrr_interview_questions: str = None  # None to start with as we may have different number of questions in the future
    pmrr_more_information: str = None  # None to start with as we may have different number of questions in the future

    @staticmethod
    def from_dict(source):
        return FirestoreConversation(**source)

    def to_dict(self):
        return asdict(self)


class OpenConversation:
    ""
    def __init__(self, firestore_conversation: FirestoreConversation, conversation_id, firestore_client):
        self.firestore_conversation = firestore_conversation
        self.name = firestore_conversation.name
        self.conversation_id = conversation_id  # TODO: Make sure this is passed

        # Attributes to update
        self.episode_done = firestore_conversation.episode_done
        self.nbr_messages = firestore_conversation.nbr_messages
        self.last_input_is_question = firestore_conversation.last_input_is_question
        self.replies_since_last_question = firestore_conversation.replies_since_last_question

        # Fika specific - draw from db or file
        self.pmrr_more_information = [c for c in
                                      firestore_conversation.pmrr_more_information]  # Split '1234 into ['1','2','3','4']
        self.change_subject = None
        self._get_more_information()  # Updates self.change_subject

        # Non fire params
        self.firestore_messages_collection = firestore_client.collection(u'messages').document(conversation_id)

        # Not used currently
        self.persona = ''
        self.persona_length = 0  # len(self.tokenizer(self.persona)['input_ids'])

    # TODO: Retrieve more information from database instead of from file
    def _get_more_information(self):
        """ Reads more information utterances from file.
        self.pmrr_more_information is used to keep track of which are left to use
        """
        with open('more_information.txt', 'r') as f:
            text = f.read()
        self.change_subject = text.split('\n')
        return

    # TODO: Make sure this is used appropriately in worlds
    def add_text(self, firestore_message: FirestoreMessage):
        """ Pushes new message to database
        """
        self.nbr_messages += 1
        msg_nbr = firestore_message.msg_nbr
        assert msg_nbr == self.nbr_messages, 'Whoopsie daisy: msg nbr in message and total nbr_messages in conversation do not match'

        doc_ref = self.firestore_messages_collection.document(msg_nbr)
        doc_ref.set(firestore_message)
        return

    def get_next_hardcoded_message(self):
        index = self.pmrr_more_information.pop(0)
        utterance = self.change_subject[index]
        return utterance

    def get_input_with_context(self):
        """ Gets the input for the model which is the last four messages of the conversation
        """
        nbr_replies_for_context = 4
        condition = self.nbr_messages - nbr_replies_for_context - 1
        docs = self.firestore_messages_collection.where('msg_nbr', '>=', condition).stream()
        messages = [doc.to_dict for doc in docs]
        messages.sort(key=lambda x: x.msg_nbr)
        context = ''
        for i, message in enumerate(messages):
            if i == len(messages - 1):  #
                context = context + message['message_en']
            else:
                context = context + message['message_en'] + '\n'

        return context

    def update_fire_object(self):
        self.firestore_conversation.episode_done = self.episode_done
        self.firestore_conversation.nbr_messages = self.nbr_messages
        self.firestore_conversation.last_input_is_question = self.last_input_is_question
        self.firestore_conversation.replies_since_last_question = self.replies_since_last_question

        pmrr = ''
        for c in self.pmrr_more_information:
            pmrr = pmrr + c
        self.firestore_conversation.pmrr_more_information = pmrr
        return

    def get_fire_object(self):
        self.update_fire_object()
        return self.firestore_conversation


class InterviewConversation:
    def __init__(self, firestore_conversation: FirestoreConversation, conversation_id, firestore_client):
        self.firestore_conversation = firestore_conversation
        self.name = firestore_conversation.name
        self.job = firestore_conversation.job
        self.conversation_id = conversation_id  # TODO: Make sure this is passed

        # Attributes to update
        self.episode_done = firestore_conversation.episode_done
        self.nbr_messages = firestore_conversation.nbr_messages
        self.last_input_is_question = firestore_conversation.last_input_is_question
        self.replies_since_last_question = firestore_conversation.replies_since_last_question

        # Fika specific - draw from db or file
        self.pmrr_interview_questions = [c for c in
                                         firestore_conversation.pmrr_more_information]  # Split '1234 into ['1','2','3','4']
        self.interview_questions = None
        self._get_interview_questions()  # Updates self.change_subject

        # Non fire params
        self.firestore_messages_collection = firestore_client.collection(u'messages').document(conversation_id)

        # Not used currently
        self.persona = ''
        self.persona_length = 0  # len(self.tokenizer(self.persona)['input_ids'])

    # TODO: Make sure this is called in worlds
    def add_text(self, firestore_message: FirestoreMessage):
        """ Pushes new message to database
        """
        self.nbr_messages += 1
        msg_nbr = firestore_message.msg_nbr
        assert msg_nbr == self.nbr_messages, 'Whoopsie daisy: msg nbr in message and total nbr_messages in conversation do not match'

        doc_ref = self.firestore_messages_collection.document(msg_nbr)
        doc_ref.set(firestore_message)
        return

    # TODO: Draw from database instead
    def _get_interview_questions(self):
        """ Reads and formats interview questions according to the job
        """
        with open('interview_questions.txt', 'r') as f:
            text = f.read()
        lines = text.split('\n')
        formatted_questions = []
        for line in lines:  # TODO: Also format skill eventually
            line = line.replace('_job_', self.job)
            formatted_questions.append(line)
        self.interview_questions = formatted_questions
        return

    def get_next_interview_question(self):
        """Pops the next question index from the pmrr_interview_questions list
           and returns the corresponding question """
        index = self.pmrr_interview_questions.pop(0)
        question = self.interview_questions[index]
        return question

    def get_input_with_context(self):
        """ Creates input for model: the conversation history since the last predefined question! """
        nbr_replies_for_context = self.replies_since_last_question * 2  #
        condition = self.nbr_messages - nbr_replies_for_context
        docs = self.firestore_messages_collection.where('msg_nbr', '>=', condition).stream()
        messages = [doc.to_dict for doc in docs]
        messages.sort(key=lambda x: x.msg_nbr)
        context = ''
        for i, message in enumerate(messages):
            if i == len(messages) - 1:  # We don't want a '\n' after the last line
                context = context + message['message_en']
            else:
                context = context + message['message_en'] + '\n'

        return context

    def update_fire_object(self):
        self.firestore_conversation.episode_done = self.episode_done
        self.firestore_conversation.nbr_messages = self.nbr_messages
        self.firestore_conversation.last_input_is_question = self.last_input_is_question
        self.firestore_conversation.replies_since_last_question = self.replies_since_last_question

        pmrr = ''
        for c in self.pmrr_interview_questions:
            pmrr = pmrr + c
        self.firestore_conversation.pmrr_interview_questions = pmrr
        return

    def get_fire_object(self):
        self.update_fire_object()
        return self.firestore_conversation
