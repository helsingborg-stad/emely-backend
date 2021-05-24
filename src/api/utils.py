import socket
from src.api.bodies import ApiMessage, BrainMessage
import logging
import requests
import threading

""" Helper functions """


def is_gcp_instance():
    """ Returns true if we're running on a GCP instance. Used for automatic authorization """
    try:
        socket.getaddrinfo('metadata.google.internal', 80)
    except socket.gaierror:
        return False
    return True


def create_error_response(error_msg):
    """ Creates a dummy BrainMessage with the error message inserted"""
    logging.warning(error_msg)
    brain_response = BrainMessage(conversation_id='',
                                  msg_id=0,
                                  lang='en',
                                  message='Oj nu blev jag lite trött och måste vila. Kan vi prata igen om en stund?',
                                  is_init_message=False,
                                  is_hardcoded=True,
                                  error_messages=error_msg)
    return brain_response


def request_task(url):
    " Helper function to wake model "
    #requests.get(url)
    dummy = ApiMessage(text='wake\nup')
    logging.warning('Waking up model by inference')
    requests.post(url=url, data=dummy.json())


def wake_model(model_url):
    " Sends a request to the model url without waiting for it"
    url = model_url + '/inference'
    threading.Thread(target=request_task, args=(url,)).start()


def create_badword_message():
    """ Creates a standard response when worlds has detected a badword in the user message """
    brain_response = BrainMessage(conversation_id='',
                                  msg_id=0,
                                  lang='sv',
                                  message='Jag förstår inte riktigt vad du menar. Ska vi gå vidare i vårt samtal?',
                                  is_init_message=False,
                                  is_hardcoded=True,
                                  error_messages='')
    return brain_response


# TODO: Implement this helper function?
def update_firestore_conversation(collection_db, firestore_conversation):
    raise NotImplementedError


# TODO: Implement this helper function?
def update_firestore_message(collection_db, firestore_message):
    raise NotImplementedError
