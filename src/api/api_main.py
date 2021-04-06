from src.chat.worlds import InterviewWorld, ChatWorld
from fastapi import FastAPI, Response, status
from argparse import Namespace

from collections import defaultdict
from src.api.models_from_bucket import download_models
from src.api.utils import is_gcp_instance
from src.api.bodys import BrainMessage, UserMessage, InitBody

brain = FastAPI()

interview_persona = Namespace(model_name='blenderbot_small-90M@f70_v2_acc20', local_model=True,
                              chat_mode='interview', no_correction=False)
fika_persona = Namespace(model_name='blenderbot_small-90M', local_model=True,
                         chat_mode='chat', no_correction=False)

interview_world = InterviewWorld(**vars(interview_persona))
fika_world = ChatWorld(**vars(fika_persona))
world = None


# Models aren't loaded
async def init_config():
    models = ['blenderbot_small-90M', 'blenderbot_small-90M@f70_v2_acc20']
    if is_gcp_instance():
        download_models(models)
        print('Downloading models from bucket')

    global interview_world, fika_world
    interview_world.load_model()
    fika_world.load_model()
    return


#brain.add_event_handler("startup", init_config)


@brain.post('/init', status_code=201)
def new_chat(msg: InitBody, response: Response):
    if msg.persona == 'fika':
        world = fika_world
    elif msg.persona == 'intervju':
        if msg.job is None:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return response
        else:
            world = interview_world
    else:
        raise NotImplementedError('There are only two personas implemented')

    greeting = world.init_conversation(conversation_id='testconv', **msg.dict())
    response = {'reply': greeting,
                'episode_done': False
                }

    # TODO: Not hardcoded
    brain_response = BrainMessage(conversation_id='test',
                                  lang='sv',
                                  message='Hello, this is a hardcoded test',
                                  is_init_message='true',
                                  hardcoded_message='true',
                                  error_messages='None')
    return brain_response


@brain.post('/fika')
def fika(msg: UserMessage):
    conversation_id = msg.conversation_id
    # TODO: Not hardcoded
    return BrainMessage(conversation_id=conversation_id,
                        lang='sv',
                        message='This is a hardcoded test message',
                        is_init_message=False,
                        hardcoded_message=True,
                        error_messages='None'
                        )


@brain.post('/intervju')
def interview(msg: UserMessage):
    conversation_id = msg.conversation_id
    # TODO: Not hardcoded
    return BrainMessage(conversation_id=conversation_id,
                        lang='sv',
                        message='This is a hardcoded test message',
                        is_init_message=False,
                        hardcoded_message=True,
                        error_messages='None')


# TODO: Deprecate in favour of post to /fika and /intervju
@brain.post('/message')
def chat(msg: UserMessage, response: Response):
    conversation_id, message, persona = msg.conversation_id, msg.message, msg.persona
    return BrainMessage(conversation_id=conversation_id,
                        lang='sv',
                        message='This is a hardcoded test message',
                        is_init_message=False,
                        hardcoded_message=True,
                        error_messages='None')
    # TODO: Deprecated?
    # if persona == 'fika':
    #     world = fika_world
    # elif persona == 'intervju':
    #     world = interview_world
    # else:
    #     response.status_code = status.HTTP_400_BAD_REQUEST
    #     return response
    #
    # try:
    #     episode_done, dialogue = world.observe(message, conversation_id)
    #     reply = world.act(dialogue)
    #     response.status_code = status.HTTP_200_OK
    # except KeyError:
    #     response.status_code = status.HTTP_404_NOT_FOUND
    #     episode_done = True
    #     reply = 'conversation_id not found'
    #
    # raise NotImplementedError('')
    # brain_response = BrainMessage()
    # return brain_response

#
# @brain.get('/init', status_code=200)
# def get_chats():
#     json_compatible_item_data = jsonable_encoder(list(world.dialogues.keys()))
#     return JSONResponse(content=json_compatible_item_data)
#
#
# @brain.get('/persona', status_code=200)
# def get_persona():
#     persona = type(world).__name__
#     response = {'reply': 'Current world is {}'.format(persona),
#                 'episode_done': True}
#     response = BaseResponse(**response)
#     return response
#
#
# @brain.put('/persona')
# def set_persona(msg: SetPersona, response: Response):
#     global world, fika_world, interview_world
#     if msg.new_persona == 'intervju' or msg.new_persona == 'interview':
#         if 'Interview' in type(world).__name__:
#             # Interview new_persona already running: HTTP already reported
#             response.status_code = 208
#         else:
#             world.unload_model()
#             world = interview_world
#             world.load_model()
#             response.status_code = status.HTTP_201_CREATED
#
#     elif msg.new_persona == 'fika':
#         if 'Chat' in type(world).__name__:
#             response.status_code = 208
#         else:
#             world.unload_model()
#             world = fika_world
#             world.load_model()
#             response.status_code = status.HTTP_201_CREATED
#     else:
#         response.status_code = status.HTTP_404_NOT_FOUND
#
#     return response
