from enum import Enum
from pydantic import BaseModel
from utils import is_gcp_instance


class PersonaEnum(str, Enum):
    intervju = 'intervju'
    fika = 'fika'


class LanguageEnum(str, Enum):
    sv = 'sv'
    en = 'en'


class InitBody(BaseModel):
    # Defines body for initial contact where a user starts a chat with Emely
    name: str
    job: str
    persona: PersonaEnum
    development_testing: bool
    webapp_local: bool
    webapp_url: str
    webapp_version: str
    webapp_git_build: str
    brain_local: bool
    brain_url: str
    lang: LanguageEnum
    password: str
    user_ip_number: str

    class Config:
        schema_extra = {
            "example": {
                "name": "Wilma",
                "job": "snickare",
                "persona": "intervju",                
                "development_testing": True,
                "webapp_local": True,
                "webapp_url": "swaggerdocs",
                "webapp_version": "NA",
                "webapp_git_build": "NA",
                "brain_local": is_gcp_instance(),
                "brain_url": "NA",
                "lang": "sv",
                "password": "KYgZfDG6P34H56WJM996CKKcNG4",
                "user_ip_number": "127.0.0.1",
            }
        }


class UserMessage(BaseModel):
    conversation_id: str
    response_time: float
    lang: LanguageEnum
    message: str
    persona: PersonaEnum
    created_at: str
    recording_used: bool
    password: str

    class Config:
        schema_extra = {
            "example": {
                "message": "This is a test message you can change",
                "conversation_id": "test",
                "response_time": -1,
                "lang": "sv",
                "password": "KYgZfDG6P34H56WJM996CKKcNG4",
            }
        }


class BrainMessage(BaseModel):
    conversation_id: str
    lang: LanguageEnum
    message: str
    is_init_message: bool
    hardcoded_message: bool
    error_messages: str
