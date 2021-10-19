import os
from src.chat.translate import ChatTranslator
from conversation import Conversation, Message, Message
from interview import DialogFlowHandler
from questions import QuestionGenerator
from database import FirestoreHandler


from filters import toxicity_filter, remove_repetition


class InterviewWorld:
    def __init__(self):
        # Set class attributes
        self._set_environment()

        self.translator = ChatTranslator()
        self.question_generator = QuestionGenerator()
        self.dialog_flow_handler = DialogFlowHandler()
        self.database_handler = FirestoreHandler()

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
        """ 
        1. Fetch conversation from firestore
        2. Checks message, translates and adds to conversation
        3. Determines which dialog block we're in and gets a reply
        4. Updates firestore and sends back reply
        """

        # 1. Fetch conversation data from firestore
        conversation = self.database_handler.get_conversation()

        # 2.
        # a) Translate
        # b) Check for badwords
        # c) Convert message to FirestoreMessage and add to conversation

        message_en = self.translator.translate()

        if toxicity_filter(message):
            # TODO: Handle this
            pass

        # TODO: Construct suplementary informaton for add_message()
        who = "user"
        conversation.add_message(message, message_en, who)

        # 3. Determine question block
        # self.dialog_flow_handler.act
        reply = self.dialog_flow_handler.act(conversation)
        # TODO:

        # 4. Update firestore with conversation and send back message to front end
        self.database_handler.update()
        return reply

