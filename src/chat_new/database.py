from dataclasses import Conversation, FirestoreMessage

class FirestoreHandler:
    # TODO: Implement this class

    def __init__(self, collection):
        self.collection = None

    def get_new_conversation_id(self) -> str:
        pass

    def get_conversation(self, conversation_id) -> Conversation:
        "Retreives a conversation from firestore"
        # TODO: Needs to return subcollection with messages too
        conversation = None
        return conversation

    def update_conversation(self, conversation):
        " Updates conversation on firestore"
        pass

