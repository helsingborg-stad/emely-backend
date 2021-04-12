from src.chat.worlds import InterviewWorld, ChatWorld
from fastapi import FastAPI, Response, status, Request
from argparse import Namespace

import subprocess
from src.api.models_from_bucket import download_models
from src.api.utils import is_gcp_instance
from src.api.bodys import BrainMessage, UserMessage, InitBody, create_error_response

brain = FastAPI()

# Variables used in the app
git_build = subprocess.check_output(["git", "rev-parse", "HEAD"]).strip().decode('utf-8')
git_version = subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"]).strip().decode('utf-8')
local_model = not is_gcp_instance()
password = 'KYgZfDG6P34H56WJM996CKKcNG4'

# Setup
interview_persona = Namespace(model_name='blenderbot_small-90M@f70_v2_acc20', local_model=local_model,
                              chat_mode='interview', no_correction=False)
fika_persona = Namespace(model_name='blenderbot_small-90M', local_model=local_model,
                         chat_mode='chat', no_correction=False)

interview_world = InterviewWorld(**vars(interview_persona))
fika_world = ChatWorld(**vars(fika_persona))
world = None


# Models aren't loaded
async def init_config():
    # Print config
    print('git build: ', git_build)
    print('local_model: ', local_model)
    print('Latest version: ', git_version)

    models = ['blenderbot_small-90M', 'blenderbot_small-90M@f70_v2_acc20']
    if is_gcp_instance():
        download_models(models)
        print('Downloading models from bucket')

    global interview_world, fika_world
    # interview_world.load_model()
    # fika_world.load_model()
    return


brain.add_event_handler("startup", init_config)


@brain.post('/init', status_code=201)
def new_chat(msg: InitBody, response: Response, request: Request):
    if not msg.password == password:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        error = 'Wrong password'
        brain_response = create_error_response(error)
    else:  # All checks pass
        # Data
        global git_build, git_version
        client_host = request.client.host
        build_data = {'brain_build': git_build, 'brain_version': git_version, 'brain_url': client_host}

        # Choose world depending on persona
        if msg.persona == 'fika':
            world = fika_world
        elif msg.persona == 'intervju':
            world = interview_world
        else:
            raise NotImplementedError('There are only two personas implemented')

        try:
            brain_response = world.init_conversation(msg, build_data=build_data)
            print('New conversation with id:', brain_response.conversation_id)
        except Exception as e:
            print(e)
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            error_msg = str(e)
            brain_response = create_error_response(error_msg)

    return brain_response


@brain.post('/fika')
def fika(msg: UserMessage, response: Response):
    # TODO: And add event loop
    if not msg.password == password:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        error = 'Wrong password'
        brain_response = create_error_response(error)
    else:
        try:
            conversation, observe_timestamp = fika_world.observe(user_request=msg)
            brain_response = fika_world.act(conversation, observe_timestamp)
        except Exception as e:
            print(e)
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            error_msg = str(e)
            brain_response = create_error_response(error_msg)
    return brain_response


@brain.post('/intervju')
def interview(msg: UserMessage, response: Response):
    # TODO: Add event loop
    if not msg.password == password:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        error = 'Wrong password'
        brain_response = create_error_response(error)
    else:
        try:
            conversation, observe_timestamp = interview_world.observe(user_request=msg)
            brain_response = interview_world.act(conversation, observe_timestamp)
        except Exception as e:
            print(e)
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            error_msg = str(e)
            brain_response = create_error_response(error_msg)
    return brain_response


