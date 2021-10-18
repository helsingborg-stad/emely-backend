import os
from src.chat.translate import ChatTranslator


class InterviewWorld:
    def __init__(self):
        # Set class attributes
        self._set_environment()

        self.translator = ChatTranslator()
        self.question_generator = QuestionGenerator()
        self.dialog_flow_handler = DialogFlowHandler(self.question_generator)

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
        
        - Generates questions
        - Determines if user wants kallprat with fika emely in the beginning of the conversation
        - Pushes data to firestore"""
        pass

    def respond(self, message: UserMessage):
        """ 
        1. Fetch conversation from firestore
        2. Checks message, translates and adds to conversation
        3. Determines which dialog block we're in and gets a reply
        4. Updates firestore and sends back reply
        """

        # 1. Fetch conversation data from firestore

        # 2.
        # a) Check for badwords
        # b) Translate
        # c) Add messages to conversation

        # 3. Determine question block
        # self.dialog_flow_handler.act

        # 4. Update firestore with conversation and send back message to front end
        pass
