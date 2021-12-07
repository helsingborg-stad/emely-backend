import pandas as pd
from pathlib import Path
from typing import List, Dict
import random
import json
import copy
import os
import logging

"""
Class for generating interview questions.

Print example usage:
    qg = QuestionGenerator()
    qlist = qg.get_interview_questions("Bartender")
    ii = 1
    for question in qlist:
        if ii==1:
            print(question["question"])
        else:
            print(question["transition"], question["question"])
        print(question["label"])
        print("")
        ii += 1
"""


class QuestionGenerator:
    def __init__(
        self, some_file="questions.xlsx", some_config="question_generator.config"
    ):
        self.question_df = pd.read_excel(
            Path(__file__).resolve().parent / some_file, engine="openpyxl"
        )
        self.question_df["question_id"] = self.question_df.index

        with open(Path(__file__).resolve().parent / some_config, "r") as file:
            config = json.load(file)

        # Set the number of different questions
        self.config = {
            "nbr_always_questions": config["nbr_always_questions"],
            "nbr_personal_questions": config["nbr_personal_questions"],
            "nbr_job_questions": config["nbr_job_questions"],
            "nbr_random_questions": config["nbr_random_questions"],
        }

        # Used for progress calculation
        nbr_interview_questions = sum(self.config.values())
        os.environ["NBR_INTERVIEW_QUESTIONS"] = str(nbr_interview_questions)

        self.nbr_alternatives = config["nbr_alternatives"]

        # Temporary variables used in question generation
        self.candidate_questions = None
        self.temp_config = None

        # Check for missing values
        assert self.question_df.isnull().values.any() == False
        for i in range(self.question_df.shape[0]):
            # Check lowercase for ","-transition
            if self.question_df.loc[i, "transition"][-1] == ",":
                for j in range(self.nbr_alternatives):
                    assert self.question_df.loc[i, f"alt_{str(j+1)}"][0].islower()
            # Check uppercase for "."-transition
            if self.question_df.loc[i, "transition"][-1] == ".":
                for j in range(self.nbr_alternatives):
                    assert self.question_df.loc[i, f"alt_{str(j+1)}"][0].isupper()

    """
    Main function of generating interview questions.
    The questions are generated semi-stochastically, using the nbr_x_questions-parameters, in the following way:
        - Filter away all questions for other jobs, and those for people with experience, if the interviewee has no experience.
        - Pick the first and last question from the dataframe among questions fulfilling fit_as_first or fit_as_last.
        - Remove these questions from the dataframe, and decrease the corresponding types self.nbr_x_questions with one.
        - Create a random order for the intermediate questions with the remaining types.
        - For each type in the generated order, retreive a corresponding question from all questions that fulfill the criterion, and remove it from the dataframe.
    When generating each question, one of self.nbr_alternatives alternatives is chosen randomly.

    Parameters:
        job     (str): Job type of the interview
        no_exp  (bool): Indicates if the interviewee has any previous job experience

    Example question:
        question = {
                "question": "Varför har du sökt det här jobbet?",
                "label": "tough",
                "transition": "Om vi nu funderar på vad som motiverar dig.",
            }
    """

    def get_interview_questions(self, job, no_exp=False) -> List[Dict[str, str]]:
        """Returns list of dicts with keys question, label, transition"""

        # Copy config
        self.temp_config = copy.copy(self.config)

        # Remove irrelevant questions
        self.candidate_questions = self.question_df[
            (self.question_df.loc[:, "job"] == job)
            | (self.question_df.loc[:, "job"] == "Allmän")
        ].copy()
        if no_exp:
            self.candidate_questions = self.candidate_questions[
                self.candidate_questions.loc[:, "fit_4_no_exp"] == True
            ]

        # If job does not exist sample random questions
        if job not in set(self.question_df.loc[:, "job"]) or job == "Allmän":
            self.temp_config["nbr_random_questions"] += self.temp_config[
                "nbr_job_questions"
            ]
            self.temp_config["nbr_job_questions"] = 0

        # We only need to return a list of question strings
        question_list = []

        # Append the first question
        first_question = self.get_first_question(
            random.randint(1, self.nbr_alternatives)
        )
        question_list.append(first_question)

        # Generate the last question
        last_question = self.get_last_question(random.randint(1, self.nbr_alternatives))

        # Create a random order of remaining question types
        question_order = []
        for _ in range(self.temp_config["nbr_always_questions"]):
            question_order.append("always")
        for _ in range(self.temp_config["nbr_personal_questions"]):
            question_order.append("personal")
        for _ in range(self.temp_config["nbr_job_questions"]):
            question_order.append("job")
        for _ in range(self.temp_config["nbr_random_questions"]):
            question_order.append("random")
        random.shuffle(question_order)

        # Append intermediate questions
        for question_type in question_order:
            try:
                next_question = self.get_intermediate_question(
                    random.randint(1, self.nbr_alternatives), question_type
                )
                question_list.append(next_question)
            except Exception as e:
                logging.error(
                    f"Failed to get question type: {question_type} for job={job} with no_exp={no_exp}"
                )
                logging.error(e)

        # Append the last question
        question_list.append(last_question)

        return question_list

    """
    Retrieve the first question in the conversation
    """

    def get_first_question(self, alt_id) -> Dict[str, str]:
        temp_df = self.candidate_questions[
            self.candidate_questions.loc[:, "fit_as_first"] == 1
        ]
        return self.get_random_question_from_df(temp_df, alt_id)

    """
    Retreive an intermediate question of a specific type
    """

    def get_intermediate_question(self, alt_id, question_type) -> Dict[str, str]:
        if question_type == "always":
            temp_df = self.candidate_questions[
                self.candidate_questions.loc[:, "always"] == 1
            ]
        elif question_type == "personal":
            temp_df = self.candidate_questions[
                self.candidate_questions.loc[:, "personal"] == 1
            ]
        elif question_type == "job":
            temp_df = self.candidate_questions[
                self.candidate_questions.loc[:, "job"] != "Allmän"
            ]
        else:  # type==random
            temp_df = self.candidate_questions[
                self.candidate_questions.loc[:, "always"] == 0
            ]
        return self.get_random_question_from_df(temp_df, alt_id)

    """
    Retrieve the last question in the conversation
    """

    def get_last_question(self, alt_id) -> Dict[str, str]:
        temp_df = self.candidate_questions[
            self.candidate_questions.loc[:, "fit_as_last"] == 1
        ]
        # Make sure two random questions are not taken if only one is allowed
        if (
            self.temp_config["nbr_random_questions"] == 0
            and self.temp_config["nbr_personal_questions"] > 0
        ):
            temp_df = temp_df[temp_df.personal == 1]
        return self.get_random_question_from_df(temp_df, alt_id)

    """
    Retreive a random question from a dataframe formatted
    """

    def get_random_question_from_df(self, temp_df, alt_id) -> Dict[str, str]:
        rand_idx = random.randint(0, temp_df.shape[0] - 1)
        question_row = temp_df.iloc[rand_idx, :]
        label = self.get_label(question_row)
        self.discard_question(question_row.question_id)
        return {
            "question": question_row.loc[f"alt_{str(alt_id)}"],
            "label": label,
            "transition": question_row.loc["transition"],
        }

    """
    Retreive the appropriate label for a specific question
    """

    def get_label(self, question_row) -> str:
        if question_row.loc["always"] == 1:
            self.temp_config["nbr_always_questions"] -= 1
            return "general"
        elif question_row.loc["personal"] == 1:
            self.temp_config["nbr_personal_questions"] -= 1
            return "personal"
        elif question_row.loc["job"] != "Allmän":
            self.temp_config["nbr_job_questions"] -= 1
            return "job"
        elif question_row.loc["tough"] == 1:
            self.temp_config["nbr_random_questions"] -= 1
            return "tough"
        else:
            self.temp_config["nbr_random_questions"] -= 1
            return "general"

    """
    Removes the question from the dataframe
    """

    def discard_question(self, question_id):
        self.candidate_questions = self.candidate_questions[
            self.candidate_questions.question_id != question_id
        ]

    def get_job_list(self):
        "Returns jobs with questions"
        job_list = list(self.question_df["job"].unique())
        job_list.remove("Allmän")
        return ["Allmän intervjuträning"] + job_list

