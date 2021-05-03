import socket
from src.api.bodies import BrainMessage
import logging

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
    logging.warn(error_msg)
    brain_response = BrainMessage(conversation_id='',
                                  msg_id=0,
                                  lang='en',
                                  message='error',
                                  is_init_message=False,
                                  is_hardcoded=True,
                                  error_messages=error_msg)
    return brain_response


# TODO: Implement this function
def update_firestore_conversation(collection_db, firestore_conversation):
    raise NotImplementedError


# TODO: Implement
def update_firestore_message(collection_db, firestore_message):
    raise NotImplementedError
