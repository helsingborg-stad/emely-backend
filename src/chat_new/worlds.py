import os
from src.chat.translate import ChatTranslator
from interview import DialogFlowHandler
from hardcoded_messages.questions import QuestionGenerator
from database import FirestoreHandler
from data import ConversationInit, Conversation, Message, UserMessage, BotMessage

from filters import contains_toxicity

# TODO: Override these with env variables in InterviewWorld._set_environment()
rasa_threshold = 0.7
rasa_enabled = False


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
        # TODO: Check if set, otherwise default to these values?
        # Suggestions:
        # LIE_FILTER, REPETITION_FILTER : turn on and off filters
        # parameters for question_generator and dialog_flow (how many turns or questions etc)
        # rasa_enabled and rasa_threshold
        env = os.environ

        ########## Filter parameters
        if "LIE_FILTER" not in env:
            env["LIE_FILTER"] = "1"
            env["LIE_THRESHOLD"] = "0.9"

        if "REPETITION_FILTER" not in env:
            env["REPETITION_FILTER"] = "1"
            env["SIMILARITY_THRESHOLD"] = "0.9"
            env["N_MESSAGES_FOR_REPETITION_FILTER"] = "8"

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

    def create_new_conversation(self, info: ConversationInit):
        """Creates a new conversation
        - Sets current_dialog_block to either intro or first question depending on parameter in info! Default to False
        - Generates questions
        - Gets first message
        - Pushes data to firestore"""
        job = info.job
        enable_small_talk = info.enable_small_talk

        question_list = self.question_generator.get_interview_questions(job)

        conversation_id = self.database_handler.get_new_conversation_id()
        new_conversation = Conversation(
            **dict(info),
            current_dialog_block="greet",
            current_dialog_block_length=0,
            conversation_id=conversation_id,
            episode_done=False,
            messages=[],
            nbr_messages=0,
            question_list=question_list,
        )

        # Get the first message
        reply = self.dialog_flow_handler.greet(new_conversation, enable_small_talk)
        reply = self.handle_bot_reply(reply, new_conversation)

        new_conversation.add_message(reply)
        self.database_handler.update(
            new_conversation
        )  # TODO Call create instead of update when it's implemented

        return reply

    def respond(self, user_message: UserMessage):
        " Responds to user"
        # TODO: Make calls async to save time!

        # Fetch conversation data from firestore
        conversation = self.database_handler.get_conversation(
            user_message.conversation_id
        )

        # Call rasa
        rasa_response = self.call_rasa(user_message)

        # Translate
        text_en = self.translator.translate(
            text=user_message.text, src=user_message.lang, target="en"
        )

        # Add usermessage to conversation
        conversation.add_user_message(user_message, text_en)

        # Toxic messages are replied to without doing anything specific.
        # Emely will pretend like she didn't understand and repeat her previous statement
        if contains_toxicity(user_message):
            # TODO: Handle this
            reply = Message()

        # If rasa detects something
        elif rasa_response["confidence"] >= rasa_threshold:
            # TODO: Set threshold using env variable?
            # TODO: Make rasa_response['message'] a BotMessage
            reply = BotMessage()

        # Let dialog flow handler act
        else:
            reply = self.dialog_flow_handler.act(conversation)

        # Translate reply depending on if it was hardcoded or not
        reply = self.handle_bot_reply(reply, conversation)

        # Add reply to conversation
        conversation.add_message(reply)
        # Update firestore with conversation and send back message to front end

        self.database_handler.update(conversation)
        return reply

    def handle_bot_reply(
        self, bot_message: BotMessage, conversation: Conversation
    ) -> Message:
        "Translates BotMessage and converts it to a proper Message object"

        # First translate depending on which way we're going
        if bot_message.lang == "en":
            text_en = bot_message.text
            text = self.translator.translate(
                text=text_en, src="en", target=conversation.lang
            )
        else:
            # TODO: Hardcoded phrases will be translated often. Add dictionary for them?
            text = bot_message.text
            text_en = self.translator.translate(
                text=text, src=bot_message.lang, target="en"
            )

        message = Message(
            **bot_message.dict(exclude={"text"}),
            conversation_id=conversation.conversation_id,
            message_nbr=conversation.get_nbr_messages(),
            text=text,
            text_en=text_en,
            progress=0,
        )

        return message

    def call_rasa(self, message):
        "Calls a rasa NLU model to identify certain questions"
        # TODO: Make async and Implement with a timeout feature so it doesn't take too long
        if rasa_enabled:
            pass
        else:
            return {"confidence": 0.0, "reply": "Hejsan tjosan"}
