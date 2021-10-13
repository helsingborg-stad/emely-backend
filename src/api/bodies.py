from enum import Enum
from pydantic import BaseModel

""" File contents: 
    Classes used to define the request bodies used to communicate with the webapp """


class PersonaEnum(str, Enum):
    """ Forces the persona field in request bodies to be valid """
    intervju = 'intervju'
    fika = 'fika'


class LanguageEnum(str, Enum):
    """ Forces lang field in request bodies to be valid """
    sv = 'sv'
    en = 'en'


class InitBody(BaseModel):
    """ Defines body for initial contact where a user starts a chat with Emely """
    name: str
    job: str = None
    created_at: str
    persona: PersonaEnum
    development_testing: bool
    webapp_local: bool
    webapp_url: str
    webapp_version: str
    brain_url: str
    lang: LanguageEnum
    user_ip_number: str
    user_id:str = None

    class Config:
        """ Default values sent when testing through swagger docs """
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
                "brain_url": "NA",
                "lang": "sv",
                "user_ip_number": "127.0.0.1",
            }
        }


class UserMessage(BaseModel):
    """Standard message from the webapp to the brain """
    conversation_id: str
    response_time: float
    lang: LanguageEnum
    message: str
    created_at: str
    recording_used: bool

    class Config:
        """ Used for the swagger docs when testing the api """
        schema_extra = {
            "example": {
                "message": "This is a test message you can change",
                "conversation_id": "__CHANGE_ME__",
                "response_time": -1,
                "created_at": '1999-04-07 18:59:24.584658',
                "recording_used": False,
                "lang": "sv",
            }
        }


class BrainMessage(BaseModel):
    """ Response body from the brain to the webapp """
    conversation_id: str
    msg_id: int
    lang: LanguageEnum
    message: str
    is_init_message: bool
    is_hardcoded: bool
    error_messages: str


class ApiMessage(BaseModel):
    """ Used to send requests to models """
    text: str
