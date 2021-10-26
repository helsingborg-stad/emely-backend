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

    def get_interview_questions(self, job) -> List[Dict[str, str]]:
        "Returns list of dicts with keys question, label, transition"
        # TODO: Implement when excel doc is ready
        # Draw appropriate questions from self.question_df in semi-random order

        # We only need to return a list of question strings
        # All of the remaining attributes are stored in the dataframe and can be
        question_list = [
            {
                "question": "Varför har du sökt det här jobbet?",
                "label": "tough",
                "transition": "Om vi nu funderar på vad som motiverar dig.",
            },
        ]

        return question_list

