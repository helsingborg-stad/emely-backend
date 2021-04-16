from src.chat.worlds import InterviewWorld, FikaWorld
from fastapi import FastAPI, Response, status, Request
from argparse import Namespace

import subprocess
from src.api.models_from_bucket import download_models
from src.api.utils import is_gcp_instance, create_error_response
from src.api.bodys import BrainMessage, UserMessage, InitBody
from pathlib import Path

""" File contents:
    FastAPI app brain that handles requests to Emely """


brain = FastAPI()

# Variables used in the app
if is_gcp_instance():
    file_path = Path(__file__).resolve().parents[2] / 'git_version.txt'
    with open(file_path, 'r') as f:
        git_version = f.read()
else:
    git_version = subprocess.check_output(["git", "describe"]).strip().decode('utf-8')
local_model = True
password = 'KYgZfDG6P34H56WJM996CKKcNG4'

# Setup
interview_persona = Namespace(model_name='blenderbot_small-90M@f70_v2_acc20', local_model=local_model,
                              chat_mode='interview', no_correction=False)
fika_persona = Namespace(model_name='blenderbot_small-90M', local_model=local_model,
                         chat_mode='chat', no_correction=False)

interview_world = InterviewWorld(**vars(interview_persona))
fika_world = FikaWorld(**vars(fika_persona))
world = None


# Models aren't loaded
async def init_config():
    """ Called when app starts """
    # Print config
    print('brain_version: ', git_version)
    print('local_model: ', local_model)

    # TODO: Deprecate when models are on GCP
    models = ['blenderbot_small-90M', 'blenderbot_small-90M@f70_v2_acc20']
    if is_gcp_instance():
        download_models(models)
        print('Downloading models from bucket')

    # TODO: Deprecate when models are on GCP
    global interview_world, fika_world
    interview_world.load_model()
    fika_world.load_model()
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
        global git_version
        client_host = request.client.host
        build_data = {'brain_version': git_version, 'brain_url': client_host}

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
async def fika(msg: UserMessage, response: Response):
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
async def interview(msg: UserMessage, response: Response):
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


