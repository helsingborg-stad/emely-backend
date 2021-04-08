from src.api.bodys import BrainMessage, UserMessage
from src.chat.conversation import FirestoreMessage

"""This script holds helper functions for converting data between different object types """


def user_message_to_firestore_message(user_message: UserMessage, translated_message, msg_nbr) -> FirestoreMessage:
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
    brain_msg = BrainMessage(conversation_id=fire_msg.conversation_id,
                             lang=fire_msg.lang,
                             message=fire_msg.message,
                             is_init_message=fire_msg.is_init_message,
                             is_hardcoded=fire_msg.is_hardcoded,
                             error_messages=fire_msg.error_messages)
    return brain_msg


