class DialogFlowHandler:
    def __init__(self):
        self.interview_model = None
        self.fika_model = None

    def _act(self, conversation):
        """ All of the methods in this class should both add the message 
        to the conversation and return it as a variable!!!!"""
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

    def _transition_to_next_block(self, conversation) -> Message:
        "Pops a new question or hardcoded message"
        if len(conversation.question_list) > 0:
            new_question = conversation.question_list.pop(0)
            conversation.current_dialog_block = new_question["label"]
            conversation.nbr_replies_since_last_question = 0

        else:
            # Transition into the goodbye block.
            return self.goodbye_block(conversation)

    def _tough_question_block(self, conversation) -> Message:
        """Should handle:
        - transition to next block
        - update conversations attributes
        """

        if transition_condition:
            return self.transition_to_next_block(conversation)

        else:
            # Action
            # self.interview_model.get_response()
            return

    def _introduction_block(self, conversation) -> Message:
        "First block of kallprat"
        pass

    def _goodbye_block(self, conversation) -> Message:
        "Last block of the interview"
        pass

    def greet(self, conversation) -> Message:
        " Gretting message. Update conversation"
        pass
