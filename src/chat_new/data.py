from typing import List, Dict
import datetime
from dataclasses import dataclass, asdict, field


@dataclass
class ConversationInit:
    brain_url: str
    created_at: str
    development_testing: bool
    lang: str
    name: str
    persona: str
    user_ip_number: str
    webapp_local: bool
    webapp_url: str
    webapp_version: str

    job: str = None
    has_experience: bool = True
    enable_small_talk: bool = True
    user_id: str = None


@dataclass
class Conversation:
    brain_url: str
    created_at: str
    current_dialog_block: str
    development_testing: bool
    episode_done: bool
    job: str
    lang: str
    name: str
    persona: str
    question_list: List[Dict]
    user_id: str
    user_ip_number: str
    webapp_local: bool
    webapp_url: str
    webapp_version: str

    # Default values
    conversation_id: str = None  # Is set first when we've pushed to firestore so it has to be None at initialisation
    current_dialog_block_length: str = 0
    messages: List = []
    nbr_messages: int = 0

    def add_message(self, message: UserMessage, who, message_en, etc):
        # TODO: What info is needed to convert UserMessage to FirestoreMessage?
        raise NotImplementedError()

    def __post_init__(self):
        persona_condition = ["fika", "intervju"]
        if self.persona not in persona_condition:
            raise ValueError(f"Persona has to be in {persona_condition}")

    def __dict__(self):
        d = asdict(self)
        d.pop("conversation_id", None)
        d.pop("messages", None)
        return d


@dataclass
class UserMessage:
    "JSON schema for API request from frontend"
    created_at: str
    conversation_id: str
    lang: str
    message: str
    recording_used: bool
    response_time: float

    def __dict__(self):
        d = asdict(self)
        d.pop("conversation_id", None)
        return d


@dataclass
class Message(UserMessage):
    "Extends Usermessage to include more data saved in database"
    conversation_id: str
    lang: str
    message_nbr: int
    message: str
    message_en: str
    progress: float
    response_time: float
    who: str

    # Default values
    created_at: str = str(datetime.datetime.now())
    dialog_block: str = None
    is_hardcoded: bool = False
    recording_used: bool = False

    def __post_init__(self):
        who_condition = ["bot", "user"]
        if self.who not in who_condition:
            raise ValueError(f"Persona has to be in {who_condition}")

