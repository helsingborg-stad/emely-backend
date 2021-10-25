from data import Message, Conversation, UserMessage, BotMessage


class DialogFlowHandler:
    def __init__(self):
        self.interview_model = None
        self.fika_model = None

    def act(self, conversation: Conversation):
        """ All of the methods in this class should filter the the message 
            and possible return something appropirate (transition to next question?) 
            if it's too short or otherwise doesn't pass the filter"""
        # TODO: Implement this and a check

        current_dialog_block = conversation.current_dialog_block

        if current_dialog_block == "tough":
            return self.tough_question_block(conversation)

        elif current_dialog_block == y:
            return self.Y_act(conversation)

        elif current_dialog_block == z:
            return self.Z_act(conversation)

        else:
            raise ValueError("Unknown dialog block")

    def _transition_to_next_block(self, conversation: Conversation) -> BotMessage:
        "Pops a new question or hardcoded message"
        if len(conversation.question_list) > 0:
            new_question = conversation.question_list.pop(0)
            conversation.current_dialog_block = new_question["label"]
            conversation.nbr_replies_since_last_question = 0

        else:
            # Transition into the goodbye block.
            return self.goodbye_block(conversation)

    def _tough_question_block(self, conversation: Conversation) -> BotMessage:
        """Should handle:
        - transition to next block
        - update conversations attributes
            - progress
            - current_dialog_block
            - current_dialog_block_length
        """

        if transition_condition:
            return self.transition_to_next_block(conversation)

        else:
            # Action
            # self.interview_model.get_response()
            return

    def _introduction_block(self, conversation: Conversation) -> BotMessage:
        "First block of kallprat"
        pass

    def _goodbye_block(self, conversation: Conversation) -> BotMessage:
        "Last block of the interview"
        pass

    def greet(self, conversation: Conversation) -> BotMessage:
        " Gretting message. Update conversation"
        # TODO: Implement. Add greetings as list in class attribute after reading from file?
        reply = BotMessage(
            conversation_id=conversation.conversation_id,
            lang=conversation.lang,
            message_nbr=conversation.nbr_messages,
            text="Hej och välkommen!",
            message_en="Hello and welcome!",
            progress=0.0,
            response_time=0.1,
            who="bot",
            is_hardcoded=True,
        )
        return reply
