from src.api.bodies import BrainMessage, UserMessage
from src.chat.conversation import FirestoreMessage, BadwordMessage
from datetime import timedelta, datetime

""" 
    File contents:
    - Helper functions 
"""


class BadwordException(Exception):
    """ Raised when user input contains a badword"""
    pass


def push_filtered_message_to_firestore(firestore_client, message: str, conversation_id: str, time: datetime,
                                       development_testing: bool):
    """ Stores message in firestore collection 'filtered_messages' """

    collection = firestore_client.collection('filtered_messages')
    badwordmessage = BadwordMessage(message=message, conversation_id=conversation_id, created_at=str(time),
                                    development_testing=development_testing)
    doc_ref = collection.document()
    doc_ref.set(badwordmessage.to_dict())
    return


def format_response_time(time: timedelta):
    """ Converts timedelta to string with seconds and one decimal place for database entry """
    return round(time.seconds + time.microseconds / 1000000, 1)


def user_message_to_firestore_message(user_message: UserMessage, translated_message, msg_nbr) -> FirestoreMessage:
    """ Converts a UserMessage to a FirestoreMessage """
    firestore_message = FirestoreMessage(conversation_id=user_message.conversation_id,
                                         msg_nbr=msg_nbr, who='user', created_at=user_message.created_at,
                                         response_time=user_message.response_time,
                                         lang=user_message.lang, message=user_message.message,
                                         message_en=translated_message,
                                         case_type='None',
                                         recording_used=user_message.recording_used, removed_from_message='',
                                         is_more_information=False,
                                         is_init_message=False, is_predefined_question=False, is_hardcoded=False,
                                         error_messages='')
    return firestore_message


def firestore_message_to_brain_message(fire_msg: FirestoreMessage) -> BrainMessage:
    """ Converts FirestoreMessage to BrainMessage """
    brain_msg = BrainMessage(conversation_id=fire_msg.conversation_id,
                             msg_id=fire_msg.msg_nbr,
                             lang=fire_msg.lang,
                             message=fire_msg.message,
                             is_init_message=fire_msg.is_init_message,
                             is_hardcoded=fire_msg.is_hardcoded,
                             error_messages=fire_msg.error_messages)
    return brain_msg


def swenglish_corrections(message: str) -> str:
    """"
    @ Isabella
    Method to fix google translate obvious faults

    Takes the english message and translates it to a more correct version of the phrase
    """
    with open("swenglish.txt", "r") as f:
        swenglish_phrases = f.readlines()
    for phrase in swenglish_phrases:
        eng, swe = phrase.split(":")[0].strip(), phrase.split(":")[1].strip()
        if eng.lower() in message.lower():
            message = message.replace(eng, swe)
    return message

def create_goodbye_message():
    """ Creates a dummy BrainMessage with the error message inserted"""
    brain_response = BrainMessage(conversation_id='',
                                  msg_id=0,
                                  lang='sv',
                                  message='Oj jag måste faktiskt gå nu. Hejdå!',
                                  is_init_message=False,
                                  is_hardcoded=True,
                                  error_messages='')
    return brain_response

