from dataclasses import Conversation, FirestoreMessage
import firebase_admin
from firebase_admin import credentials, firestore

from src.api.utils import is_gcp_instance


class FirestoreHandler:
    # TODO: Implement this class

    def __init__(self, collection):
        self._authenticate_firebase()

        # Authenticate firebase to connect to firestore
        self.firestore_collection = self.firestore_client.collection("conversations")

    def _authenticate_firebase(self):
        "Authenticates on firebase"
        # TODO: Change projectId and api-key when moving this to new gcp project
        if is_gcp_instance():
            if not firebase_admin._apps:
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred, {"projectId": "emelybrainapi",})

            self.firestore_client = firestore.client()

        # Running locally -> use service account with json
        else:
            if not firebase_admin._apps:
                json_path = (
                    Path(__file__)
                    .resolve()
                    .parents[2]
                    .joinpath("emelybrainapi-33194bec3069.json")
                )
                cred = credentials.Certificate(json_path.as_posix())
                firebase_admin.initialize_app(cred)

            self.firestore_client = firestore.client()

    def get_new_conversation_id(self) -> str:
        "Makes a document reference in database and returns it's unique id"
        doc_ref = self.firestore_collection.document()
        return doc_ref.id

    def create_new_conversation(self, current_dialog_block, question_list, **kwargs)
        doc_ref = self.firestore_collection.document()
        
        new_conversation = Conversation(
            **kwargs,
            current_dialog_block=current_dialog_block,
            conversation_id=doc_ref.id,
            question_list=question_list,
        )


    def get_conversation(self, conversation_id) -> Conversation:
        "Retreives a conversation from firestore"
        # TODO: Needs to return subcollection with messages too
        doc_ref = self.firestore_colleciotn.document(conversation_id)

        conversation = None
        return conversation

    def update_conversation(self, conversation):
        " Updates conversation on firestore"
        pass

