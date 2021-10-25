from typing import List, Optional, Dict
import datetime
from dataclasses import asdict
from pydantic import BaseModel

# TODO: Remove progress from message classes. Keep in Conversation. Still send back to webapp


class UserMessage(BaseModel):
    "JSON schema for API request from frontend"
    created_at: str
    conversation_id: str
    lang: str
    message: str
    recording_used: bool
    response_time: float

    class Config:
        """ Default values sent when testing through swagger docs """

        schema_extra = {
            "example": {
                "created_at": "1999-01-01 00:00:00.000000",
                "conversation_id": "123456789",
                "lang": "sv",
                "message": "Hej Emely",
                "recording_used": False,
                "response_time": 0.0,
            }
        }


class BotMessage(BaseModel):
    is_hardcoded: bool
    lang: str
    text: str
    response_time: float

    # Default values
    created_at: str = str(datetime.datetime.now())
    recording_used: bool = False
    who: str = "bot"


class Message(BaseModel):
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
    # dialog_block: str = None
    is_hardcoded: Optional[bool]
    recording_used: bool = False

    def to_dict(self):
        return self.dict(exclude={"conversation_id"})


class ConversationInit(BaseModel):
    "Defines JSON schema for init requests"
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

    job: Optional[str] = None
    has_experience: Optional[bool] = True
    enable_small_talk: Optional[bool] = True
    user_id: Optional[str] = None

    class Config:
        """ Default values sent when testing through swagger docs """

        schema_extra = {
            "example": {
                "brain_url": "null",
                "created_at": "1999-04-07 18:59:24.584658",
                "development_testing": True,
                "lang": "sv",
                "name": "swaggerdocs",
                "persona": "intervju",
                "user_ip_number": "127.0.0.1",
                "webapp_local": True,
                "webapp_url": "null",
                "webapp_version": "null",
                "job": None,
                "has_experience": True,
                "enable_small_talk": True,
                "user_id": None,
            }
        }


class Conversation(BaseModel):
    brain_url: str
    created_at: str
    current_dialog_block: str
    current_dialog_block_length: str
    development_testing: bool
    episode_done: bool
    job: str
    lang: str
    messages: List
    name: str
    nbr_messages: int
    persona: str
    question_list: List
    user_id: str
    user_ip_number: str
    webapp_local: bool
    webapp_url: str
    webapp_version: str

    # Default values
    conversation_id: str = None  # Is set first when we've pushed to firestore so it has to be None at initialisation
    progress: float = 0

    def add_message(self, message: Message):
        # TODO: Enum for typing message

        self.nbr_messages += 1
        self.messages.append(message)
        return

    def add_user_message(self, user_message: UserMessage, message_en: str):
        message = Message(
            **user_message.dict(),
            message_en=message_en,
            message_nbr=self.nbr_messages,
            who="user",
            is_hardcoded=False,
            progress=self.progress
        )

        self.add_message(message)
        return

    def to_dict(self):
        return self.dict(
            exclude={"messages"}
        )  # Messags will be saved in sub collection

    def get_all_messages(self) -> List[Message]:
        pass

    def get_last_two_messages(self) -> Dict[int, Message]:
        sorted_messages = sorted(
            self.messages, key=lambda x: x.message_nbr, reverse=True
        )

        if self.nbr_messages == 1:
            return {0: self.messages[0]}
        else:
            last_two_message = sorted_messages[:2]
            return {m.message_nbr: m for m in last_two_message}

