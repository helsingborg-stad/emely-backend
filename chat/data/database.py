from chat.data.types import Conversation, Message
import firebase_admin
from firebase_admin import credentials, firestore
from pathlib import Path

from chat.utils import is_gcp_instance


class FirestoreHandler:
    "Contains firestore connection and methods for creating, updating and retrieving data"

    def __init__(self):
        self._authenticate_firebase()

        # Authenticate firebase to connect to firestore
        self.firestore_collection = self.firestore_client.collection(
            "conversations-with-emely"
        )

    def _authenticate_firebase(self):
        "Authenticates firebase"
        # TODO: Change projectId and api-key when moving this to new gcp project
        if is_gcp_instance():
            if not firebase_admin._apps:
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred, {"projectId": "emely-gcp",})

            self.firestore_client = firestore.client()

        # Running locally -> use service account with json
        else:
            if not firebase_admin._apps:
                json_path = (
                    Path(__file__)
                    .resolve()
                    .parents[2]
                    .joinpath("emely-gcp-b2705e7ec5a0.json")
                )
                cred = credentials.Certificate(json_path.as_posix())
                firebase_admin.initialize_app(cred)

            self.firestore_client = firestore.client()

    def get_new_conversation_id(self) -> str:
        "Makes a document reference in database and returns it's unique id"
        doc_ref = self.firestore_collection.document()
        return doc_ref.id

    def get_conversation(self, conversation_id) -> Conversation:
        "Retreives a conversation from firestore"
        # TODO: Async calls?
        conversation_ref = self.firestore_collection.document(conversation_id)
        firestore_conversation = conversation_ref.get().to_dict()

        # Messages
        # TODO: All messages are fetched. Is there a better way to do this?
        message_collection = conversation_ref.collection("messages")
        message_refs = message_collection.where("message_nbr", ">=", 0).stream()
        firestore_messages = [doc.to_dict() for doc in message_refs]
        messages = [
            Message(**m, conversation_id=conversation_id) for m in firestore_messages
        ]

        conversation = Conversation(**firestore_conversation, messages=messages,)

        return conversation

    def create(self, conversation):
        "creates a new conversation in firestore"
        conversation_ref = self.firestore_collection.document(
            conversation.conversation_id
        )
        conversation_ref.set(conversation.to_dict(only_updatable=False))

        messages = conversation.get_last_two_messages()
        message_collection = conversation_ref.collection("messages")
        for message_nbr, message in messages.items():
            message_ref = message_collection.document(str(message_nbr))
            message_ref.set(message.to_dict())
        return

    def update(self, conversation: Conversation):
        " Updates conversation on firestore"

        conversation_ref = self.firestore_collection.document(
            conversation.conversation_id
        )

        conversation_ref.update(conversation.to_dict(only_updatable=True))

        messages = conversation.get_last_two_messages()
        message_collection = conversation_ref.collection("messages")
        for message_nbr, message in messages.items():
            message_ref = message_collection.document(str(message_nbr))
            message_ref.set(message.to_dict())
        return
