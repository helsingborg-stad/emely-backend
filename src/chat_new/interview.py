from data import Message, Conversation, UserMessage, BotMessage
from models import InterviewModel, FikaModel
from filters import is_too_repetitive, remove_lies
from hardcoded_messages import greetings, goodbyes
import logging

import random


tough_question_max_length = 5
personal_question_max_length = 3
general_question_max_length = 3
job_question_max_length = 3
small_talk_max_length = 3

interview_model_context_length = 8
fika_model_context_length = 8


class DialogFlowHandler:
    "Object that encapsulates all methods relating to dialog flow"

    def __init__(self):
        self.interview_model = InterviewModel()
        self.fika_model = FikaModel()

    def act(self, conversation: Conversation):
        """ All of the methods in this class should filter the the message 
            and possible return something appropirate (transition to next question?) 
            if it's too short or otherwise doesn't pass the filter"""
        # TODO: Add filters at the end of this method? Env variables for activating them?

        current_dialog_block = conversation.current_dialog_block

        if conversation.episode_done:
            return self.goodbye_block(conversation)

        if current_dialog_block == "greet":
            if conversation.enable_small_talk:
                bot_message = self.smalltalk_block(conversation)
            else:
                bot_message = self.transition_to_next_block(conversation)

        elif current_dialog_block == "tough":
            bot_message = self.question_block(
                conversation, max_length=tough_question_max_length
            )

        elif current_dialog_block == "personal":
            bot_message = self.question_block(
                conversation, max_length=personal_question_max_length
            )

        elif current_dialog_block == "job":
            bot_message = self.question_block(
                conversation, max_length=job_question_max_length
            )

        elif current_dialog_block == "general":
            bot_message = self.question_block(
                conversation, max_length=general_question_max_length
            )

        elif current_dialog_block == "smalltalk":
            bot_message = self.smalltalk_block(conversation)

        else:
            raise ValueError("Unknown dialog block")

        # Increment dialog block length
        conversation.current_dialog_block_length += 1

        return bot_message

    def transition_to_next_block(self, conversation: Conversation) -> BotMessage:
        "Pops a new question or hardcoded message and moves into the next block"
        if len(conversation.question_list) > 0:

            new_question = conversation.question_list.pop(0)
            text = new_question["transition"] + new_question["question"]

            # Update attributes
            conversation.current_dialog_block = new_question["label"]
            conversation.current_dialog_block_length = 0

            bot_message = BotMessage(
                is_hardcoded=True, lang=conversation.lang, text=text, response_time=0,
            )

            return bot_message

        # Transition into the goodbye block.
        else:
            return self.goodbye_block(conversation)

    def question_block(self, conversation: Conversation, max_length) -> BotMessage:
        """Handles a question_block by:
        1. Checking if it's time to transition: true -> transition_to_next_block
        2. Requests inference from interview model
        3. Post filtering of model reply which can lead to transition_to_next_block if the filter makes it too short
        """

        if conversation.current_dialog_block_length > max_length:
            return self.transition_to_next_block(conversation)

        else:
            # Action
            context = conversation.get_last_x_message_strings(
                interview_model_context_length
            )
            model_reply, response_time = self.interview_model.get_response(context)
            reply = BotMessage(
                lang="en",
                text=model_reply,
                response_time=response_time,
                is_hardcoded=True,
            )
            # Post filtering of model replies
            if is_too_repetitive(reply, conversation):
                logging.warning("Early transition to next block due to repetitiveness")
                return self.transition_to_next_block(conversation)
            elif remove_lies(reply):
                logging.warning("Early transition to next block due lying")
                return self.transition_to_next_block(conversation)

            return reply

    def smalltalk_block(self, conversation: Conversation) -> BotMessage:
        "First block of small talk. Uses the fika model instead of the Interview Model"
        if conversation.current_dialog_block_length > small_talk_max_length:
            return self.transition_to_first_question(conversation)

        else:
            # Action
            context = conversation.get_last_x_message_strings(
                interview_model_context_length
            )
            model_reply, response_time = self.fika_model.get_response(context)
            reply = BotMessage(
                lang="en",
                text=model_reply,
                response_time=response_time,
                is_hardcoded=True,
            )
            return reply

    def transition_to_first_question(self, conversation: Conversation) -> BotMessage:
        "Should be used when transitioning from smalltalk to first question"
        new_question = conversation.question_list.pop(0)
        transition = random.choice(greetings.first_transition)
        text = transition + new_question["question"]

        # Update attributes
        conversation.current_dialog_block = new_question["label"]
        conversation.current_dialog_block_length = 0

        bot_message = BotMessage(
            is_hardcoded=True, lang=conversation.lang, text=text, response_time=0,
        )

        return bot_message

    def goodbye_block(self, conversation: Conversation) -> BotMessage:
        "Last block of the interview"
        conversation.episode_done = True
        goodbye = random.choice(goodbyes.interview)
        reply = BotMessage(
            lang=conversation.lang, text=goodbye, response_time=0.0, is_hardcoded=True,
        )
        return reply

    def greet(self, conversation: Conversation) -> BotMessage:
        "Greeting message"

        if conversation.enable_smalltalk:
            greeting = random.choice(greetings.interview_smalltalk).format(
                conversation.name
            )

        else:
            greeting = random.choice(greetings.interview_no_smalltalk).format(
                conversation.name
            )

        return BotMessage(
            lang=conversation.lang, text=greeting, response_time=0.1, is_hardcoded=True,
        )
