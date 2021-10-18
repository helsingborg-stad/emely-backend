class DialogFlowHandler:
    def __init__(self, question_generator):
        self.question_generator
        self.interview_model = None
        self.fika_model = None

    def act(self, conversation):
        " Determines which method to call"

        current_dialog_block = conversation.current_dialog_block

        if current_dialog_block == "tough":
            return self.tough_question_block(conversation)

        elif current_dialog_block == y:
            return self.Y_act(conversation)

        elif current_dialog_block == z:
            return self.Z_act(conversation)

        else:
            raise ValueError("Unknown dialog block")

    def transition_to_next_block(self, conversation) -> Message:
        "Pops a new question or hardcoded message"
        if len(conversation.question_list) > 0:
            new_question = conversation.question_list.pop(0)
            conversation.current_dialog_block = new_question["label"]
            conversation.nbr_replies_since_last_question = 0

        else:
            # Transition into the goodbye block.
            return self.goodbye_block(conversation)

    def tough_question_block(self, conversation) -> Message:
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

    def introduction_block(self, conversation) -> Message:
        "First block of kallprat"
        pass

    def goodbye_block(self, conversation) -> Message:
        "Last block of the interview"
        pass

