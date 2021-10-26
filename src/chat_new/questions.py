import pandas as pd
from pathlib import Path
from typing import List, Dict
import random


class QuestionGenerator:
    # TODO: Replace questions.xlsx with real excel file
    def __init__(self, some_file="questions.xlsx"):
        self.question_df = pd.read_excel(Path(__file__).resolve().parent / some_file)

        # Set the number of different questions
        # TODO: Automatically from some config?
        self.nbr_tough_questions = 2
        self.nbr_personal_questions = 1
        self.nbr_job_questions = 2

        # TODO: Assert that the df is properly formatted?
        # All values should be proper and duplicated questions should have the same attributes

    def get_interview_questions(self, job) -> List[str]:
        # TODO: Implement when excel doc is ready
        # Draw appropriate questions from self.question_df in semi-random order

        # We only need to return a list of question strings
        # All of the remaining attributes are stored in the dataframe and can be
        question_list = [
            {"question": "Varför har du sökt det här jobbet?", "label": "tough"},
            {"question": "Hur är du som person?", "label": "personal"},
        ]

        return question_list

    # def get_question_attributes(self, question: str) -> Dict:
    #     """Used to retrieve the attributes to a question. Needed to identify the appropriate question block later

    #     """

    #     # Find row in self.question_df
    #     question_attributes = self.question_df[self.question_df.question == question]

    #     if len(question_attributes) == 0:
    #         raise ValueError("Found no matching questions in question_df")

    #     # Some questions are duplicated for several jobs. We'll pick the first
    #     elif len(question_attributes) > 1:
    #         question_attributes = question_attributes.loc[0]

    #     return dict(question_attributes)

