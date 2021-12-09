import os
import logging
from chat.translate.translator import ChatTranslator
from chat.fika.flow import FikaFlowHandler

from chat.interview.flow import InterviewFlowHandler
from chat.interview.questions import QuestionGenerator

from chat.data.database import FirestoreHandler
from chat.data.types import (
    ConversationInit,
    Conversation,
    Message,
    UserMessage,
    BotMessage,
)

import random
from chat.hardcoded_messages import rasa, callstoaction
from chat.dialog.models import RasaModel
from chat.dialog.filters import contains_toxicity


class DialogWorld:
    def __init__(self):
        # Set class attributes
        self._set_environment()

        self.translator = ChatTranslator()
        self.question_generator = QuestionGenerator()
        self.interview_flow_handler = InterviewFlowHandler()
        self.fika_flow_handler = FikaFlowHandler()
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

        if "USE_HUGGINGFACE_FIKA" not in env:
            env["USE_HUGGINGFACE_FIKA"] = "0"
            env["HUGGINGFACE_KEY"] = ""

        if "MIN_ANSWER_LENGTH" not in env:
            env["MIN_ANSWER_LENGTH"] = "7"

        ########## Filter parameters
        if "LIE_FILTER" not in env:
            env["LIE_FILTER"] = "1"
            env["LIE_THRESHOLD"] = "0.9"

        if "REPETITION_FILTER" not in env:
            env["REPETITION_FILTER"] = "1"
            env["SIMILARITY_THRESHOLD"] = "0.9"
            env["N_MESSAGES_FOR_REPETITION_FILTER"] = "8"

        if "RASA_ENABLED" not in env:
            env["RASA_ENABLED"] = "1"
            self.rasa_threshold = env.get("RASA_THRESHOLD", 0.9)

        logging.info("ENVIRONMENT VARIABLES:")
        for k, v in env.items():
            logging.info(f"{k}: {v}")

    def wake_models(self):
        """Wakes all MLModels.
        Can be coupled with an API endpoint in the webserver so front end can wake everything
        """
        self.rasa_model.wake_up()
        self.interview_flow_handler.interview_model.wake_up()
        if os.environ["USE_HUGGINGFACE_FIKA"] == "1":
            self.interview_flow_handler.huggingface_fika_model.wake_up()
        self.interview_flow_handler.fika_model.wake_up()
        return

    async def create_new_conversation(self, info: ConversationInit):
        """Creates a new conversation
        - Sets current_dialog_block to either intro or first question depending on parameter in info! Default to False
        - Generates questions
        - Gets first message
        - Pushes data to firestore"""
        persona = info.persona
        if persona == "intervju":
            job = info.job
            question_list = self.question_generator.get_interview_questions(job)
        elif persona == "fika":
            question_list = []

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
        if persona == "intervju":
            reply = self.interview_flow_handler.greet(new_conversation)
            reply = await self.handle_bot_reply(reply, new_conversation)
        elif persona == "fika":
            reply = self.fika_flow_handler.greet(new_conversation)
            reply = await self.handle_bot_reply(reply, new_conversation)

        progress = new_conversation.add_message(reply)
        self.database_handler.create(new_conversation)
        reply.progress = progress
        return reply

    async def interview_reply(self, user_message: UserMessage):
        "Responds to user in an interview"

        # Call rasa
        # TODO: Make the calls to rasa, translate and database concurrent
        rasa_response = await self.rasa_model.get_response(user_message)

        # Translate
        text_en = await self.translator.translate(
            text=user_message.text, src=user_message.lang, target="en"
        )

        # Fetch conversation data from firestore
        conversation = self.database_handler.get_conversation(
            user_message.conversation_id
        )

        # Replies that aren't added to the conversation
        if len(user_message.text) < float(os.environ["MIN_ANSWER_LENGTH"]) and not conversation.current_dialog_block=="small_talk":
            return Message(
                is_hardcoded=True,
                lang="sv",
                response_time=0,
                conversation_id=user_message.conversation_id,
                message_nbr=conversation.get_nbr_messages() - 1,
                text=random.choice(callstoaction.tooshort),
                text_en="Please elaborate and write a longer answer so I understand",
                who="bot",
            )
        elif contains_toxicity(user_message):
            return Message(
                is_hardcoded=True,
                lang="sv",
                response_time=0,
                conversation_id=user_message.conversation_id,
                message_nbr=conversation.get_nbr_messages() - 1,
                text=conversation.repeat_last_message(),
                text_en="You said a bad word to me",
                who="bot",
            )

        # Add usermessage to conversation
        conversation.add_user_message(user_message, text_en)

        if (
            rasa_response["confidence"] >= self.rasa_threshold
            and rasa_response["name"] in rasa.intents
        ):
            intent = rasa_response["name"]
            reply = self.interview_flow_handler.rasa_act(intent, conversation)

        # Let dialog flow handler act
        else:
            reply = self.interview_flow_handler.act(conversation)

        # Translate reply depending on if it was hardcoded or not
        reply = await self.handle_bot_reply(reply, conversation)

        # Add reply to conversation
        progress = conversation.add_message(reply)
        # Update firestore with conversation and send back message to front end

        self.database_handler.update(conversation)  # TODO: Fire and forget
        reply.progress = progress
        return reply

    async def fika_reply(self, user_message: UserMessage):
        "Responds to user during fika"
        # Translate
        # TODO: Concurrent calls to database and translate
        text_en = await self.translator.translate(
            text=user_message.text, src=user_message.lang, target="en"
        )

        # Fetch conversation data from firestore
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
                who="bot",
            )
        else:
            reply = self.fika_flow_handler.act(conversation)

        # Translate reply depending on if it was hardcoded or not
        reply = await self.handle_bot_reply(reply, conversation)

        # Add reply to conversation
        progress = conversation.add_message(reply)
        # Update firestore with conversation and send back message to front end

        self.database_handler.update(conversation)  # TODO: Fire and forget
        reply.progress = progress
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
        )

        return message
