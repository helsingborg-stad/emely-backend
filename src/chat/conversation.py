from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class FirestoreMessage(object):
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
    name: str
    persona: str
    nbr_messages: int = 0
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
    episode_done: bool = False
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
    # TODO: Switch Firestore
    def __init__(self, conversation: FirestoreConversation, tokenizer):
        self.fire = fire
        self.name = fire.name
        self.conversation_id = fire.conversation_id

        self.conversation_sv = BlenderConversation(user_text=fire.user_text_sv, bot_text=fire.bot_text_sv,
                                                   tokenizer=tokenizer)
        self.conversation_en = BlenderConversation(user_text=fire.user_text_en, bot_text=fire.bot_text_en,
                                                   tokenizer=tokenizer)

        self.episode_done = fire.episode_done
        self.change_subject = fire.change_subject

        # Non fire params
        self.tokenizer = tokenizer
        self.persona = ''
        self.persona_length = 0  # len(self.tokenizer(self.persona)['input_ids'])

    def get_context(self):
        context = '{}\n{}'.format(self.persona, self.conversation_en.get_dialogue_history(30))
        return context

    def get_fire_object(self):
        fika_firestore = FikaFirestore(conversation_id=self.fire.conversation_id,
                                       name=self.name,
                                       episode_done=self.episode_done,
                                       bot_text_sv=self.conversation_sv.bot_text,
                                       user_text_sv=self.conversation_sv.user_text,
                                       bot_text_en=self.conversation_en.bot_text,
                                       user_text_en=self.conversation_en.user_text,
                                       change_subject=self.change_subject)
        return fika_firestore


class InterviewConversation:
    # TODO: Switch Firestore
    def __init__(self, fire: InterviewFirestore, tokenizer):
        self.fire = fire
        self.conversation_id = fire.conversation_id
        self.name = fire.name
        self.job = fire.job

        self.conversation_sv = BlenderConversation(user_text=fire.user_text_sv, bot_text=fire.bot_text_sv,
                                                   tokenizer=tokenizer)
        self.conversation_en = BlenderConversation(user_text=fire.user_text_en, bot_text=fire.bot_text_en,
                                                   tokenizer=tokenizer)

        self.nbr_replies = fire.nbr_replies
        self.last_input_is_question = fire.last_input_is_question
        self.episode_done = fire.episode_done
        self.questions = fire.questions
        self.tokenizer = tokenizer
        self.persona = 'your persona: My name is Emely and I am an AI interviewer'
        self.persona_length = len(self.tokenizer(self.persona)['input_ids'])
        self.more_information = fire.more_information

    def one_step_back(self):
        self.conversation_sv.pop()
        self.conversation_sv.pop()
        self.conversation_en.pop()
        self.conversation_en.pop()
        self.nbr_replies -= 1
        return self.conversation_sv.bot_text[-1]

    def get_context(self):
        # context = '{}\n{}'.format(self.persona, self.conversation_en.get_dialogue_history(40))
        context = self.conversation_en.get_nbr_interactions(self.nbr_replies)
        return context

    def get_fire_object(self):
        #
        interview_firestore = InterviewFirestore(conversation_id=self.fire.conversation_id,
                                                 name=self.name,
                                                 job=self.job,
                                                 episode_done=self.episode_done,
                                                 bot_text_sv=self.conversation_sv.bot_text,
                                                 user_text_sv=self.conversation_sv.user_text,
                                                 bot_text_en=self.conversation_en.bot_text,
                                                 user_text_en=self.conversation_en.user_text,
                                                 more_information=self.more_information,
                                                 questions=self.questions,
                                                 last_input_is_question=self.last_input_is_question,
                                                 nbr_replies=self.nbr_replies
                                                 )
        return interview_firestore


class BlenderConversation:

    def __init__(self, bot_text, user_text, tokenizer):
        self.bot_text = bot_text
        self.user_text = user_text
        self.user_turn = None
        self.tokenizer = tokenizer

    def add_user_text(self, text):
        if self.user_turn or self.user_turn is None:
            self.user_text.append(text)
            self.user_turn = False
        else:
            raise ValueError("It's the bot's turn to add a reply to the conversation")
        return

    def add_bot_text(self, text):
        if not self.user_turn or self.user_turn is None:
            self.bot_text.append(text)
            self.user_turn = True
        else:
            raise ValueError("It's the user's turn to add an input to the conversation")
        return

    def pop(self):
        if self.user_turn:
            self.bot_text.pop()
            self.user_turn = False
        else:
            self.user_text.pop()
            self.user_turn = True
        return

    def get_dialogue_history(self, max_len=120):
        # Returns string of the dialogue history with bot and user inputs separated with '\n'
        # max_len set to default 100 as model has max input length 128 and we want some space for new input
        history = ''
        tokens_left = max_len
        if self.user_turn:
            # Start backwards from bot_text
            for i in reversed(range(len(self.user_text))):
                bot_text = self.bot_text[i]
                user_text = self.user_text[i]
                nbr_tokens = len(self.tokenizer(bot_text)['input_ids']) + len(self.tokenizer(user_text)['input_ids'])
                if nbr_tokens < tokens_left:  # This is not fool proof as the model tokenizer tokenizes differently
                    history = user_text + '\n' + bot_text + '\n' + history
                    tokens_left -= (nbr_tokens + 2)
                else:
                    break

        else:
            # Start backwards from user_text
            history = self.user_text[-1]
            tokens_left -= len(self.tokenizer(history)['input_ids'])
            for i in reversed(range(len(self.user_text) - 1)):
                bot_text = self.bot_text[i]
                user_text = self.user_text[i]
                nbr_tokens = len(self.tokenizer(bot_text)['input_ids']) + len(self.tokenizer(user_text)['input_ids'])
                if nbr_tokens < tokens_left:
                    history = user_text + '\n' + bot_text + '\n' + history
                    tokens_left -= (nbr_tokens + 2)
                else:
                    break
        return history

    def to_txt(self, description, file, error=None):
        # Writes the dialogue to txt file in subdirectory
        text = '####################################\n' + 'Conversation description: ' + description + '\n\n'
        if self.user_turn:
            for i in range(len(self.user_text)):
                text = text + 'User>>> ' + self.user_text[i] + '\n Bot>>> ' + self.bot_text[i] + '\n'
        else:
            for i in range(len(self.bot_text)):
                text = text + 'User>>> ' + self.user_text[i] + '\n Bot>>> ' + self.bot_text[i] + '\n'
            text = text + 'User>>> ' + self.user_text[-1]

        if error is None:
            text = text + '\n\n'
        else:
            text = text + '\n' + 'Terminated due to {}'.format(error) + '\n\n'

        with open(file, 'a') as f:
            f.write(text)
        return

    def print_dialogue(self):
        # Prints the dialogue
        text = ''
        if self.user_turn:
            for i in range(len(self.user_text)):
                text = text + 'User>>> ' + self.user_text[i] + '\n Bot>>> ' + self.bot_text[i] + '\n'
        else:
            for i in range(len(self.bot_text)):
                text = text + 'User>>> ' + self.user_text[i] + '\n Bot>>> ' + self.bot_text[i] + '\n'
            text = text + 'User>>> ' + self.user_text[-1]

            print(text)
        return

    def get_nbr_interactions(self, nbr):
        """Retrieves only the last nbr interactions in the conversation as a string formatted with \n separators"""
        lines = deque()
        assert not self.user_turn  # Needs to be bots turn for this method to be used
        for i in range(nbr + 1):
            backindex = -1 - i
            lines.appendleft(self.user_text[backindex])
            lines.appendleft(self.bot_text[backindex])
        context = ''
        for line in lines:
            context = context + line + '\n'
        context = context.rsplit('\n', 1)[0]
        return context

    def get_bot_replies(self):
        return self.bot_text

    def get_user_replies(self):
        return self.user_text


def read_questions(file_path):
    # Reads interview questions from a text file, one question per line. '{}' in place where job should be inserted
    with open(file_path, 'r') as f:
        questions = f.readlines()
    format_this = [True if '{}' in question else False for question in questions]
    return zip(questions, format_this)
