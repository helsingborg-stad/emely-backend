from typing import List, Optional, Dict
import datetime
from pydantic import BaseModel, Field
import os
import chat


class UserMessage(BaseModel):
    "JSON schema for API request from frontend"
    created_at: str
    conversation_id: str
    lang: str
    text: str
    recording_used: bool
    response_time: float

    class Config:
        """ Default values sent when testing through swagger docs """

        schema_extra = {
            "example": {
                "created_at": "1999-01-01 00:00:00.000000",
                "conversation_id": "123456789",
                "lang": "sv",
                "text": "Hej Emely",
                "recording_used": False,
                "response_time": 0.0,
            }
        }


class BotMessage(BaseModel):
    "Data class for messages generated by Emely in DialogFlowHander"
    is_hardcoded: bool
    lang: str
    text: str
    response_time: float

    # Default values
    created_at: str = str(datetime.datetime.now())
    recording_used: bool = False
    who: str = "bot"
    filtered_message: str = None
    filtered_reason: str = None


class Message(BaseModel):
    "Extends BotMessage and UserMessage. Incldues more data that is saved in the database"
    conversation_id: str
    lang: str
    message_nbr: int
    text: str
    text_en: str
    response_time: float
    show_emely: bool
    who: str

    # Default values
    created_at: str = str(datetime.datetime.now())
    is_hardcoded: Optional[bool]
    progress: float = 0
    recording_used: bool = False
    filtered_message: str = None
    filtered_reason: str = None
    rasa_intent: str = None

    def to_dict(self):
        "Used before pushing to database"
        return self.dict(exclude={"conversation_id"})


class ConversationInit(BaseModel):
    "Defines JSON schema for init requests"
    created_at: str
    development_testing: bool
    lang: str
    name: str
    persona: str
    user_ip_number: str
    use_huggingface: bool

    job: Optional[str] = Field(None, title="job for interview conversation")
    has_experience: Optional[bool] = Field(True, title="If user has work experience")
    enable_small_talk: Optional[bool] = Field(True, title="enables small talk")
    user_id: Optional[str] = Field(None, title="user id")

    class Config:
        """ Default values sent when testing through swagger docs """

        schema_extra = {
            "example": {
                "created_at": "1999-04-07 18:59:24.584658",
                "development_testing": True,
                "lang": "sv",
                "name": "swaggerdocs",
                "persona": "intervju",
                "user_ip_number": "127.0.0.1",
                "job": "Snickare",
                "has_experience": True,
                "enable_small_talk": True,
                "user_id": None,
            }
        }


class Conversation(BaseModel):
    "Dataclass with information about a conversation"
    created_at: str
    current_dialog_block: str
    current_dialog_block_length: int
    development_testing: bool
    enable_small_talk: bool
    episode_done: bool
    job: str
    lang: str
    messages: List
    name: str
    nbr_messages: int
    persona: str
    question_list: List
    user_id: Optional[str] = Field(None)
    user_ip_number: str
    use_huggingface: bool

    # Default values
    conversation_id: str = None  # Is set first when we've pushed to firestore so it has to be None at initialisation
    progress: float = 0

    def add_message(self, message: Message) -> float:
        """Adds a message to the conversation and computes progress. 
        Progress is many of the interview questions you've gone through so far"""
        if self.episode_done:
            progress = 1
        elif self.persona == "intervju":
            total_questions = os.environ.get("NBR_INTERVIEW_QUESTIONS", 5)
            questions_left_ratio = len(self.question_list) / int(total_questions)
            # Small talk phase
            if questions_left_ratio == 1:
                progress = 0.07
            else:
                progress = (
                    1 - (questions_left_ratio) - 0.05
                )  # Remove a little bit since we don't want 1

        else:
            progress = self.nbr_messages / (chat.fika.flow.max_dialog_length + 1)

        self.nbr_messages += 1
        self.messages.append(message)
        self.progress = progress
        return progress

    def add_user_message(
        self,
        user_message: UserMessage,
        text_en: str,
        rasa_intent: str = None
        show_emely: bool,
        filtered_reason: str = None,
    ):
        "Adds a UserMessage to conversation by first converting it to a Message"
        if not show_emely:
            assert filtered_reason != None
        message = Message(
            **user_message.dict(),
            text_en=text_en,
            message_nbr=self.nbr_messages,
            who="user",
            is_hardcoded=False,
            rasa_intent=rasa_intent,
            show_emely=show_emely,
            filtered_reason=filtered_reason,
        )

        self.add_message(message)
        return

    def to_dict(self, only_updatable):
        """Used before pushing conversation to database. 
        Removes the message list as it's saved in subcollection"""
        if only_updatable:
            return self.dict(
                include={
                    "current_dialog_block",
                    "current_dialog_block_length",
                    "episode_done",
                    "nbr_messages",
                    "question_list",
                    "progress",
                }
            )
        else:
            return self.dict(
                exclude={"messages"}
            )  # Messags will be saved in sub collection

    def get_emely_messages(self, N=-1) -> List[str]:
        "Returns a list of all Messages uttered by Emely in english"
        emely_messages = [m.text_en for m in self.messages if m.who == "bot"]
        if N == -1 or N >= len(emely_messages):
            return emely_messages
        else:
            return emely_messages[-N:]

    def get_last_two_messages(self) -> Dict[int, Message]:
        "Used before updating database since only two messages are new and need to be synced"

        if self.nbr_messages == 1:
            return {0: self.messages[0]}
        else:
            sorted_messages = sorted(
                self.messages, key=lambda x: x.message_nbr, reverse=True
            )
            last_two_message = sorted_messages[:2]
            return {m.message_nbr: m for m in last_two_message}

    def get_last_x_message_strings(self, x):
        " Returns blenderbot formatted string of last x messages"
        sorted_messages = sorted(
            self.messages, key=lambda x: x.message_nbr, reverse=False
        )
        filtered_messages = filter(lambda message: message.show_emely, sorted_messages)

        # We will take all
        if x >= len(sorted_messages):
            messages = filtered_messages

        else:
            messages = filtered_messages[-x:]

        strings = [m.text_en for m in messages]
        return "\n".join(strings)

    def get_nbr_messages(self) -> int:
        return len(self.messages)

    def repeat_last_message(self) -> str:
        "Gets last message. Used when user says badword"
        for i in range(1, 3):
            recent_message = self.messages[-i]
            if recent_message.who == "bot":
                latest_emely_message = recent_message
                break
        assert latest_emely_message.is_hardcoded
        return latest_emely_message.text

    def last_bot_message_was_hardcoded(self) -> str:
        "Returns true if Emelys last message was hardcoded"
        for i in range(1, 3):
            recent_message = self.messages[-i]
            if recent_message.who == "bot":
                latest_emely_message = recent_message
                break
        return latest_emely_message.is_hardcoded
