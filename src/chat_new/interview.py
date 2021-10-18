

class DialogFlowHandler:
    def __init__(self, question_generator):
        self.question_generator
        self.interview_model = None
        self.fika_model = None

    def _determine_dialog_block(self, conversation) -> str:
        "Determines which question block"

        if "All questions are left":
            return "starting phase"
        elif "No questions are left":
            return "end phase"

        # -> we are in a question block!
        # use question attributes to determine dialog (question) block
        question_attributes = self.question_generator.get_question_attributes()

        if cond == x:
            return "X"

        elif cond == y:
            return "Y"

        elif cond == z:
            return "Z"

        else:
            raise ValueError("Could not determine question block")

    def act(self, conversation):

        dialog_block = self._determine_dialog_block(conversation)

        if dialog_block == x:
            return self.X_act(conversation)

        elif dialog_block == y:
            return self.Y_act(conversation)

        elif dialog_block == z:
            return self.Z_act(conversation)

        else:


    def X_act(self, conversation) -> Message:
        """Should handle:
        - transition to next block
        - update conversations attributes
        """

        if transition:
            return self.transition_to_next_block(conversation)

        elif cond == X:
            # Action
            # self.interview_model.get_response()
            return

    def transition_to_next_block(self, conversation) -> Message:
        "Pops a new question or hardcoded message"
