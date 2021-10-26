from data import Message, Conversation, UserMessage, BotMessage
from models import InterviewModel, FikaModel

tough_question_max_length = 5
personal_question_max_length = 3
general_question_max_length = 3
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
        # TODO: Implement this and a check

        current_dialog_block = conversation.current_dialog_block

        if current_dialog_block == "greet":
            return self.transition_to_next_block(conversation)

        elif current_dialog_block == "tough":
            return self.question_block(
                conversation, max_length=tough_question_max_length
            )

        elif current_dialog_block == "personal":
            return self.question_block(
                conversation, max_length=personal_question_max_length
            )

        elif current_dialog_block == "general":
            return self.question_block(
                conversation, max_length=general_question_max_length
            )

        elif current_dialog_block == "smalltalk":
            return self.smalltalk_block(conversation)

        else:
            raise ValueError("Unknown dialog block")

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

        else:
            # Transition into the goodbye block.
            return self.goodbye_block(conversation)

    def question_block(self, conversation: Conversation, max_length) -> BotMessage:
        """Should handle:
        - transition to next block
        - update conversations attributes
            - progress
            - current_dialog_block
            - current_dialog_block_length
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

            # TODO: Implement and put some sort of filter here that can lead to transition_to_next_block

            return reply

    def smalltalk_block(self, conversation: Conversation) -> BotMessage:
        "First block of small talk"
        # TODO: Implement. Use small_talk_max_length
        pass

    def goodbye_block(self, conversation: Conversation) -> BotMessage:
        "Last block of the interview"
        # TODO: Variation
        reply = BotMessage(
            lang=conversation.lang,
            text="Tack för att jag fick intervju dig! Hejdå!",
            response_time=0.0,
            is_hardcoded=True,
        )
        return reply

    def greet(self, conversation: Conversation, enable_small_talk: bool) -> BotMessage:
        " Gretting message. Update conversation"
        # TODO: Implement. Add greetings as list in class attribute after reading from file?
        # TODO: Enable small talk -> two different paths
        if enable_small_talk:
            text = "Hej och välkommen!"
            return BotMessage(
                lang=conversation.lang, text=text, response_time=0.1, is_hardcoded=True,
            )
        else:
            # TODO: Transition into next block, i.e. first interview question, immediately
            text = "Hej och välkommen! Vi börjar direkt med din intervju"
            return BotMessage(
                lang=conversation.lang, text=text, response_time=0.1, is_hardcoded=True,
            )
