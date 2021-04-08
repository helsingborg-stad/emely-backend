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
    # interview_world.load_model()
    fika_world.load_model()
    return


brain.add_event_handler("startup", init_config)


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
            # TODO: Remove this when init works for interviewworld
            brain_response = BrainMessage(conversation_id='test',
                                          lang='sv',
                                          message='Hello, this is a hardcoded test for interviewworld which isn not done',
                                          is_init_message='true',
                                          is_hardcoded='true',
                                          error_messages='None')
            return brain_response
    else:
        raise NotImplementedError('There are only two personas implemented')

    brain_response = world.init_conversation(msg)

    return brain_response


@brain.post('/fika')
def fika(msg: UserMessage):
    conversation_id = msg.conversation_id
    # TODO: Not hardcoded
    conversation, observe_timestamp = fika_world.observe(user_request=msg)
    brain_response = fika_world.act(conversation, observe_timestamp)
    return BrainMessage(conversation_id=conversation_id,
                        lang='sv',
                        message='This is a hardcoded test message',
                        is_init_message=False,
                        is_hardcoded=True,
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
                        is_hardcoded=True,
                        error_messages='None')


# TODO: Deprecate in favour of post to /fika and /intervju
@brain.post('/message')
def chat(msg: UserMessage, response: Response):
    conversation_id, message, persona = msg.conversation_id, msg.message, msg.persona
    return BrainMessage(conversation_id=conversation_id,
                        lang='sv',
                        message='This is a hardcoded test message',
                        is_init_message=False,
                        is_hardcoded=True,
                        error_messages='None')
