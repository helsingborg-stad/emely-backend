from src.chat.worlds import InterviewWorld, ChatWorld
from fastapi import FastAPI, Response, status
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


class BaseResponse(BaseModel):
    response_code: int
    reply: str
    episode_done: bool


class BrainResponse(BaseModel):
    # brain_version: float
    response: BaseResponse
    # reply_to_local_message_id: str


class SetPersona(BaseModel):
    new_persona: str



interview_persona = Namespace(model_name='blenderbot_small-90M@8', local_model=True,
                              chat_mode='interview')
fika_persona = Namespace(model_name='blenderbot-400M-distill', local_model=True,
                         chat_mode='chat')

# Models aren't loaded
interview_world = InterviewWorld(**vars(interview_persona))
fika_world = InterviewWorld(**vars(fika_persona))

world = interview_world  # Automatically choose this?
world.load_model()

@brain.post('/message')
def chat(msg: Message):
    user_message, conversation_id = msg.message, msg.conversation_id
    if msg.conversation_id in world.interviews.keys():
        episode_done = world.observe(user_message, conversation_id)
        reply = world.act(conversation_id)

        response = {'reply': reply,
                    'response_code': 200,
                    'episode_done': episode_done
                    }
    else:  # Conversation id doesn't exist
        response = {'reply': "The session/conversation id doesn't exist, please use init first",
                    'response_code': 404,
                    'episode_done': True}
    response = BaseResponse(**response)
    brain_response = {'response': response}
    brain_response = BrainResponse(**brain_response)
    return brain_response


@brain.post('/init')
def new_chat(msg: InitChat):
    conversation_id, name, job = msg.conversation_id, msg.name, msg.job
    greeting = world.init_conversation(conversation_id, name, job)
    response = {'reply': greeting,
                'response_code': 200,
                'episode_done': False
                }
    response = BaseResponse(**response)
    brain_response = {'response': response}
    brain_response = BrainResponse(**brain_response)
    return brain_response

@brain.get('/persona')
def get_persona():
    persona = type(world).__name__
    response = {'reply': 'Current world is {}'.format(persona),
                'response_code': 200,
                'episode_done': True}
    response = BaseResponse(**response)
    return response

@brain.put('/persona')
def set_persona(msg: SetPersona, response: Response):
    global world
    if msg.new_persona == 'intervju' or msg.new_persona == 'interview':

        if 'Interview' in type(world).__name__:
            # Interview new_persona already running: HTTP already reported
            response.status_code = 208
        else:
            world.unload_model()
            world = fika_world
            world.load_model()
            response.status_code = status.HTTP_201_CREATED

    elif msg.new_persona == 'fika':

        if 'Chat' in type(world).__name__:
            response.status_code = 208
        else:
            world.unload_model()
            world = fika_world
            world.load_model()
            response.status_code = status.HTTP_201_CREATED
    else:
        response.status_code = status.HTTP_404_NOT_FOUND

    return response
