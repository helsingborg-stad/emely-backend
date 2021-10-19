import os
from src.chat.translate import ChatTranslator
from conversation import Conversation, Message, Message
from interview import DialogFlowHandler
from questions import QuestionGenerator
from database import FirestoreHandler

from filters import contains_toxicity


class InterviewWorld:
    def __init__(self):
        # Set class attributes
        self._set_environment()

        self.translator = ChatTranslator()
        self.question_generator = QuestionGenerator()
        self.dialog_flow_handler = DialogFlowHandler()
        self.database_handler = FirestoreHandler()
        self.rasa_model = "https://rasa-nlu-ef5bmjer3q-ey.a.run.app"

    def _set_environment(self):
        "Sets class attributes based on environment variables"
        # TODO
        pass

    def wake_models(self):
        """Wakes all MLModels. 
        Can be coupled with an API endpoint in the webserver so front end can wake everything 
        """
        # TODO
        # self.interview_model.wake_up()
        # self.fika_model.wake_up()
        # self.rasa_model.wake_up()
        return

    def create_new_conversation(self, info: InitBody):
        """Creates a new conversation
        - Sets current_dialog_block to either intro or first question depending on parameter in info! Default to False
        - Generates questions
        - Gets first message
        - Pushes data to firestore"""
        job = info.job
        current_dialog_block = None  # TODO: Set based on field in InitBody?

        question_list = self.question_generator.get_interview_questions(job)

        conversation_id = self.database_handler.get_new_conversation_id()
        new_conversation = Conversation(
            **info,
            current_dialog_block=current_dialog_block,
            conversation_id=conversation_id,
            question_list=question_list,
        )

        # Get the first message
        reply = self.dialog_flow_handler.greet(new_conversation)
        self.database_handler.update(new_conversation)

        return reply

    def respond(self, message: UserMessage):
        " Responds to user"

        # Fetch conversation data from firestore
        conversation = self.database_handler.get_conversation()

        # Call rasa
        rasa_response = self.call_rasa(message)  # TODO: Make async to save time!

        # Translate
        message_en = self.translator.translate()

        # Add usermessage to conversation
        # TODO: Construct suplementary informaton for add_message()
        who = "user"
        conversation.add_message(message, message_en, who)

        # Toxic messages are replied to without doing anything specific.
        # Emely will pretend like she didn't understand and repeat her previous statement
        if contains_toxicity(message):
            # TODO: Handle this
            reply = Message()

        # If rasa detects something
        elif rasa_response["confidence"] > threshold:
            # TODO: Set threshold using env variable?
            # TODO: Make rasa_response['message'] a user message
            rasa_reply = Message()
            reply = rasa_reply

        # Let dialog flow handler act
        else:
            reply = self.dialog_flow_handler.act(conversation)

        # Add reply to conversation
        conversation.add_message(reply)
        # Update firestore with conversation and send back message to front end

        self.database_handler.update()
        return reply

    async def call_rasa(self, message):
        if rasa_enabled:
            # TODO: Implement with a timeout feature so it doesn't take too long
            pass
        else:
            return {"confidence": 0.0, "reply": "Hejsan tjosan"}
