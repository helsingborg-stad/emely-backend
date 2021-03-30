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
    brain_local: bool
    lang: LanguageEnum
    webapp_version: str
    password: str
    user_ip_number: str

    class Config:
        schema_extra = {
            "example": {
                "name": "Wilma",
                "persona": "intervju",
                "job": "snickare",
                "development_testing": True,
                "webapp_local": True,
                "webapp_url": "swaggerdocs",
                "webapp_version": "NA",
                "brain_local": is_gcp_instance(),
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
