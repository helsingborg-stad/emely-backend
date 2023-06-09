from chat.data.types import Conversation, BotMessage
from chat.dialog.models import FikaModel, HuggingfaceFika
from chat.hardcoded_messages import greetings, goodbyes
import logging
import os

import random

goodbye_words = ["hej då", "hejdå"]
personas = [
    "your persona:my name is Emely\nyour persona:i speak Swedish\nyour persona:i like horses\n",
    "your persona:my name is Emely\nyour persona:i speak Swedish\nyour persona:i am a computer geek\n",
    "your persona:my name is Emely\nyour persona:i speak Swedish\nyour persona:i like hockey\n",
    "your persona:my name is Emely\nyour persona:i speak Swedish\nyour persona:i like snow\n",
    "your persona:my name is Emely\nyour persona:i speak Swedish\nyour persona:i like summer\n",
]
fika_model_context_length = 8
max_dialog_length = 40

fika_block_list = ["it's not a good way to live",
    "that's not a good way to live",
    "in bed",
    "children with my child",
]

class FikaFlowHandler:
    "Object that encapsulates methods for fika dialog flow"

    def __init__(self):
        self.fika_model = FikaModel()
        self.huggingface_fika_model = HuggingfaceFika()
        self.goodbye_words = goodbye_words
        self.persona = random.choice(personas)

    def act(self, conversation: Conversation):
        "Requests response from fika model"
        last_user_message = conversation.get_last_x_message_strings(1)
        if (
            any([word in last_user_message for word in self.goodbye_words])
            or conversation.nbr_messages > max_dialog_length
        ):
            return self.goodbye(conversation)

        context = self.persona + conversation.get_last_x_message_strings(
            fika_model_context_length
        )
        if conversation.use_huggingface:
            try:
                model_reply, response_time = self.huggingface_fika_model.get_response(
                    context
                )
            except:
                model_reply, response_time = self.fika_model.get_response(context, fika_block_list)
        else:
            model_reply, response_time = self.fika_model.get_response(context, fika_block_list)
        reply = BotMessage(
            lang="en",
            text=model_reply,
            response_time=response_time,
            is_hardcoded=False,
            filtered_reason="",
            filtered_message="",
        )
        # Post filtering of model replies
        # if is_too_repetitive(reply, conversation):
        #     logging.warning("Transitioning to new fika subject due to repetitivness")
        #     return self.transition_to_new_subject(conversation)

        return reply

    def transition_to_new_subject(self, conversation):
        "Used to get a hardcoded message for 'changing the subject' if Emely gets stuck saying the same stuff"
        pass

    def goodbye(self, conversation: Conversation):
        conversation.episode_done = True
        goodbye = random.choice(goodbyes.fika)
        reply = BotMessage(
            lang=conversation.lang,
            text=goodbye,
            response_time=0.0,
            is_hardcoded=True,
            filtered_reason="",
            filtered_message="",
        )
        return reply

    def greet(self, conversation: Conversation):
        name = conversation.name
        if name == "":
            greeting = random.choice(greetings.fika)
        else:
            greeting = random.choice(greetings.fika_name_formatted).format(name)
        return BotMessage(
            lang=conversation.lang,
            text=greeting,
            response_time=0.0,
            is_hardcoded=True,
            filtered_reason="",
            filtered_message="",
        )

