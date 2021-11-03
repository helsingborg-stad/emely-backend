import os
from translator import ChatTranslator
from interview import DialogFlowHandler
from hardcoded_messages.questions import QuestionGenerator
from hardcoded_messages import rasa
from database import FirestoreHandler
from data import ConversationInit, Conversation, Message, UserMessage, BotMessage
from models import RasaModel
from database import FirestoreHandler
from data import ConversationInit, Conversation, Message, UserMessage, BotMessage

from filters import contains_toxicity

# TODO: Override these with env variables in DialogWorld._set_environment()
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
        self.rasa_model = RasaModel()
        self.wake_models()

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
        self.rasa_model.wake_up()
        self.dialog_flow_handler.interview_model.wake_up()
        self.dialog_flow_handler.fika_model.wake_up()
        return

    async def create_new_conversation(self, info: ConversationInit):
        """Creates a new conversation
        - Sets current_dialog_block to either intro or first question depending on parameter in info! Default to False
        - Generates questions
        - Gets first message
        - Pushes data to firestore"""
        job = info.job

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
        reply = self.dialog_flow_handler.greet(new_conversation)
        reply = await self.handle_bot_reply(reply, new_conversation)

        new_conversation.add_message(reply)
        self.database_handler.update(
            new_conversation
        )  # TODO Call create instead of update when it's implemented

        return reply

    async def respond(self, user_message: UserMessage):
        " Responds to user"
        # Call rasa
        # TODO: ASync
        rasa_response = await self.rasa_model.get_response(user_message)

        # Translate
        # TODO: ASync?
        text_en = await self.translator.translate(
            text=user_message.text, src=user_message.lang, target="en"
        )

        # Fetch conversation data from firestore
        # TODO: ASync
        conversation = self.database_handler.get_conversation(
            user_message.conversation_id
        )

        # Add usermessage to conversation
        conversation.add_user_message(user_message, text_en)

        # Toxic messages are replied to without doing anything specific.
        # Emely will pretend like she didn't understand and repeat her previous statement
        if contains_toxicity(user_message):
            return Message(
                is_hardcoded=True,
                lang="sv",
                response_time=0,
                conversation_id=conversation.conversation_id,
                message_nbr=-1,
                text=conversation.repeat_last_message(),
                text_en="You said a bad word to me",
                progress=0,
            )

        # If rasa detects something
        elif (
            rasa_response["confidence"] >= rasa_threshold
            and rasa_response["name"] in rasa.replies.keys()
        ):
            key = rasa_response["name"]
            text = rasa.replies[key]
            reply = BotMessage(is_hardcoded=True, lang="sv", text=text, response_time=0)

        # Let dialog flow handler act
        else:
            # TODO: ASync
            reply = self.dialog_flow_handler.act(conversation)

        # Translate reply depending on if it was hardcoded or not
        reply = await self.handle_bot_reply(reply, conversation)

        # Add reply to conversation
        conversation.add_message(reply)
        # Update firestore with conversation and send back message to front end

        self.database_handler.update(conversation)
        return reply

    async def handle_bot_reply(
        self, bot_message: BotMessage, conversation: Conversation
    ) -> Message:
        "Translates BotMessage and converts it to a proper Message object"

        # First translate depending on which way we're going
        if bot_message.lang == "en":
            text_en = bot_message.text
            text = await self.translator.translate(
                text=text_en, src="en", target=conversation.lang
            )
        else:
            # TODO: Hardcoded phrases will be translated often. Add dictionary for them?
            text = bot_message.text
            text_en = await self.translator.translate(
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
