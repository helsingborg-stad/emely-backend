from enum import Enum
from pydantic import BaseModel


class PersonaEnum(str, Enum):
    intervju = 'intervju'
    fika = 'fika'


class LanguageEnum(str, Enum):
    sv = 'sv'
    en = 'en'


class UserMessage(BaseModel):
    conversation_id: str
    response_time: str
    lang: LanguageEnum
    message: str
    created_at: str
    recording_used: bool
    password: str

    class Config:
        schema_extra = {
            "example": {
                "message": "This is a test message you can change",
                "conversation_id": "__CHANGE_ME__",
                "response_time": '-1',
                "created_at": '1999-04-07 18:59:24.584658',
                "recording_used": False,
                "lang": "sv",
                "password": "KYgZfDG6P34H56WJM996CKKcNG4",
            }
        }


class InitBody(BaseModel):
    # Defines body for initial contact where a user starts a chat with Emely
    name: str
    job: str
    created_at: str
    persona: PersonaEnum
    development_testing: bool
    webapp_local: bool
    webapp_url: str
    webapp_version: str
    webapp_git_build: str
    brain_url: str
    lang: LanguageEnum
    password: str
    user_ip_number: str

    class Config:
        schema_extra = {
            "example": {
                "name": "Wilma",
                "job": "snickare",
                "created_at": '1999-04-07 18:59:24.584658',
                "persona": "fika",
                "development_testing": True,
                "webapp_local": True,
                "webapp_url": "swaggerdocs",
                "webapp_version": "NA",
                "webapp_git_build": "NA",
                "brain_url": "NA",
                "lang": "sv",
                "password": "KYgZfDG6P34H56WJM996CKKcNG4",
                "user_ip_number": "127.0.0.1",
            }
        }


class BrainMessage(BaseModel):
    conversation_id: str
    lang: LanguageEnum
    message: str
    is_init_message: bool
    is_hardcoded: bool
    error_messages: str
