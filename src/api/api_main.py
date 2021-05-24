from src.chat.worlds import InterviewWorld, FikaWorld
from fastapi import FastAPI, Response, status, Request
from argparse import Namespace

import subprocess
from src.api.utils import is_gcp_instance, create_error_response, create_badword_message
from src.chat.utils import BadwordException
from src.api.bodies import BrainMessage, UserMessage, InitBody
from pathlib import Path
import logging
import timeit
import uvicorn
import traceback

""" File contents:
    FastAPI app brain that handles requests to Emely """

brain = FastAPI()
logging.basicConfig(level=logging.NOTSET)

# Variables used in the app
if is_gcp_instance():
    # TODO: Solve smoother
    file_path = Path(__file__).resolve().parents[2] / 'git_version.txt'
    with open(file_path, 'r') as f:
        git_version = f.read()
else:
    git_version = subprocess.check_output(["git", "describe", "--tags"]).strip().decode('utf-8')
password = 'KYgZfDG6P34H56WJM996CKKcNG4'

interview_world: InterviewWorld
fika_world: FikaWorld
world = None


async def init_config():
    """ Called when app starts """
    # Print config
    print('brain_version: ', git_version)

    # TODO: Time to deprecate this functionallity?
    # Setup
    interview_persona = Namespace(no_correction=False)
    fika_persona = Namespace(no_correction=False)

    global interview_world, fika_world
    interview_world = InterviewWorld(**vars(interview_persona))
    fika_world = FikaWorld(**vars(fika_persona))
    return


brain.add_event_handler("startup", init_config)


@brain.post('/init', status_code=201)
def new_chat(msg: InitBody, response: Response, request: Request):
    if not msg.password == password:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        error = 'Wrong password'
        error_response = create_error_response(error)
        return error_response
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
            response.status_code = status.HTTP_400_BAD_REQUEST
            error = "Invalid persona: only fika and intervju available"
            error_response = create_error_response(error)
            return error_response

        try:
            brain_response = world.init_conversation(msg, build_data=build_data)
            print('New conversation with id:', brain_response.conversation_id)
        except Exception as e:
            print(traceback.format_exc())
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            error_msg = str(e)
            brain_response = create_error_response(error_msg)

    return brain_response


@brain.post('/fika')
async def fika(msg: UserMessage, response: Response):

    try:
        conversation, observe_timestamp = fika_world.observe(user_request=msg)
        brain_response = fika_world.act(conversation, observe_timestamp)
        return brain_response

    # Badword in the user message
    except BadwordException as e:
        response.status_code = status.HTTP_403_FORBIDDEN
        badword_response = create_badword_message()
        logging.warning('Found badword. Check database')
        return badword_response

    except Exception as e:
        print(traceback.format_exc())
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_msg = str(e)
        error_response = create_error_response(error_msg)
        return error_response


@brain.post('/intervju')
async def interview(msg: UserMessage, response: Response):

    try:
        conversation, observe_timestamp = interview_world.observe(user_request=msg)
        brain_response = interview_world.act(conversation, observe_timestamp)
        return brain_response

    # TODO: This is the same as for fika. Maybe we should also repeat the previous input?
    except BadwordException as e: 
        response.status_code = status.HTTP_403_FORBIDDEN
        badword_response = create_badword_message()
        logging.warning('Found badword. Check database')
        return badword_response

    except Exception as e:
        print(traceback.format_exc())
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_msg = str(e)
        error_response = create_error_response(error_msg)
        return error_response



if __name__ == '__main__':
    uvicorn.run(brain, log_level='info')
