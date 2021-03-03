from src.chat.worlds import InterviewWorld, ChatWorld
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Optional, List
from argparse import Namespace

brain = FastAPI()


class Message(BaseModel):
    # Defines regular message during chat
    conversation_id: int
    message: str


class InitChat(BaseModel):
    # Defines body for initial contact where a user starts a chat with Emely
    conversation_id: int
    name: str
    job: str


class Response(BaseModel):
    response_code: int
    reply: str
    episode_done: bool


class BrainResponse(BaseModel):
    # brain_version: float
    response: Response
    # reply_to_local_message_id: str


kwargs = Namespace(name='Alex', job='programmerare',
                   model_name='blenderbot_small-90M', local_model=True,
                   chat_mode='interview')

world = InterviewWorld(**vars(kwargs))


@brain.post('/')
def new_chat(msg: InitChat):
    conversation_id, name, job = msg.conversation_id, msg.name, msg.job
    greeting = world.init_conversation(conversation_id, name, job)
    reply = {'conversation.conversation_id': msg.conversation_id,
             'message': greeting}
    return Message(**reply)


@brain.post('/')
def chat(msg: Message):
    user_message, conversation_id = msg.message, msg.conversation_id
    episode_done = world.observe(user_message, conversation_id)
    reply = world.act(conversation_id)

    response = {'reply': reply,
                'response_code': 200,
                'episode_done': episode_done
                }
    response = Response(**response)
    brain_response = {'response': response}
    brain_response = BrainResponse(**brain_response)
    return brain_response
