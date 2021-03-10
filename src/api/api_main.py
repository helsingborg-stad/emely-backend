from src.chat.worlds import InterviewWorld, ChatWorld
from fastapi import FastAPI, Response, status
from pydantic import BaseModel
from argparse import Namespace
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


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
    reply: str
    episode_done: bool


class BrainResponse(BaseModel):
    # brain_version: float
    response: BaseResponse
    # reply_to_local_message_id: str


class SetPersona(BaseModel):
    new_persona: str


brain = FastAPI()

interview_persona = Namespace(model_name='blenderbot_small-90M@8', local_model=True,
                              chat_mode='interview')
fika_persona = Namespace(model_name='blenderbot-400M-distill', local_model=True,
                         chat_mode='chat')

interview_world = InterviewWorld(**vars(interview_persona))
fika_world = ChatWorld(**vars(fika_persona))
world = None


# Models aren't loaded
async def init_config():
    global interview_world, fika_world, world
    world = interview_world  # Automatically choose this?
    world.load_model()
    return


brain.add_event_handler("startup", init_config)


@brain.post('/message')
def chat(msg: Message, response: Response):
    conversation_id, message = msg.conversation_id, msg.message
    try:
        episode_done = world.observe(message, conversation_id)
        reply = world.act(conversation_id)
        response.status_code = status.HTTP_200_OK
    except KeyError:
        response.status_code = status.HTTP_404_NOT_FOUND
        episode_done = True
        reply = ''
        return response
    response = BaseResponse(reply=reply, episode_done=episode_done)
    brain_response = BrainResponse(response=response)
    return brain_response


@brain.post('/init', status_code=201)
def new_chat(msg: InitChat, response: Response):
    greeting = world.init_conversation(**msg.dict())
    response = {'reply': greeting,
                'episode_done': False
                }
    response = BaseResponse(**response)
    brain_response = {'response': response}
    brain_response = BrainResponse(**brain_response)
    return brain_response


@brain.get('/init', status_code=200)
def get_chats():
    json_compatible_item_data = jsonable_encoder(list(world.dialogues.keys()))
    return JSONResponse(content=json_compatible_item_data)


@brain.get('/persona', status_code=200)
def get_persona():
    persona = type(world).__name__
    response = {'reply': 'Current world is {}'.format(persona),
                'episode_done': True}
    response = BaseResponse(**response)
    return response


@brain.put('/persona')
def set_persona(msg: SetPersona, response: Response):
    global world, fika_world, interview_world
    if msg.new_persona == 'intervju' or msg.new_persona == 'interview':
        if 'Interview' in type(world).__name__:
            # Interview new_persona already running: HTTP already reported
            response.status_code = 208
        else:
            world.unload_model()
            world = interview_world
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
