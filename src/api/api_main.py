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

interview_world: InterviewWorld
fika_world: FikaWorld
world = None

# Response
migraine_response = 'Ojoj mitt stackars huvud... Jag tror jag har bivit sjuk och måste gå till vårdcentralen. Vi får prata en annan dag. Hejdå!'


async def init_config():
    """ Called when app starts """
    # Print config
    print('brain_version: ', git_version)

    global interview_world, fika_world
    interview_world = InterviewWorld()
    fika_world = FikaWorld()
    return


brain.add_event_handler("startup", init_config)


@brain.post('/init', status_code=201)
def new_chat(msg: InitBody, response: Response, request: Request):
    # Request is missing job
    if msg.persona == 'intervju' and msg.job == None:
        response.status_code == status.HTTP_400_BAD_REQUEST
        message = 'Av någon anledning har jag glömt vilket jobb du skulle söka... Prova att klicka på knappen \'återställ dialog\' snett upp till vänster'
        error_msg = 'Init to intervju is missing job information'
        error_response = create_error_response(message, error_msg)
        return error_response

    # All checks pass
    else:  
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
            error_msg = "Invalid persona: only fika and intervju available"
            message = 'Just nu har jag bara två olika personas: fika och intervju'
            error_response = create_error_response(message, error_msg)
            return error_response

        try:
            brain_response = world.init_conversation(msg, build_data=build_data)
            print('New conversation with id:', brain_response.conversation_id)
        except Exception as e:
            print(traceback.format_exc())
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            error_msg = str(e)
            brain_response = create_error_response(message=migraine_response, error_msg=error_msg)

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
        error_response = create_error_response(message=migraine_response, error_msg=error_msg)
        return error_response


@brain.post('/intervju')
async def interview(msg: UserMessage, response: Response):

    try:
        conversation, observe_timestamp, intent = interview_world.observe(user_request=msg)
        brain_response = interview_world.act(conversation, observe_timestamp, intent)
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
        error_response = create_error_response(message=migraine_response, error_msg=error_msg)
        return error_response

@brain.get('/joblist')
def get_joblist():
    return {"occupations": get_occupations()}

def get_occupations():
    competences_list_path = Path(__file__).resolve().parent.parent / 'chat' / 'core_competences.txt'
    with open(competences_list_path, "r") as f:
        competences = f.readlines()
    jobs = []
    for line in competences:
        jobs.append(line.split(":")[0])
    return jobs

if __name__ == '__main__':
    uvicorn.run(brain, log_level='warning')
