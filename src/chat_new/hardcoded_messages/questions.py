import pandas as pd
from pathlib import Path
from typing import List, Dict
import random
import json

'''
Class for generating interview questions.
'''
class QuestionGenerator:
    def __init__(self, some_file="questions.xlsx", some_config="question_generator.config"):
        self.question_df = pd.read_excel(Path(__file__).resolve().parent / some_file, engine='openpyxl')
        self.question_df['question_id'] = self.question_df.index

        with open(Path(__file__).resolve().parent / some_config,"r") as file:
            config = json.load(file)

        # Set the number of different questions
        self.nbr_always_questions = config["nbr_always_questions"]
        self.nbr_personal_questions = config["nbr_personal_questions"]
        self.nbr_job_questions = config["nbr_job_questions"]
        self.nbr_random_questions = config["nbr_random_questions"]

        self.n_alternatives = config["n_alternatives"]

        # TODO: Assert that the df is properly formatted?
        # All values should be proper and duplicated questions should have the same attributes

    '''
    Main function of generating interview questions.
    The questions are generated semi-stochastically, using the nbr_x_questions-parameters, in the following way:
        - Filter away all questions for other jobs, and those for people with experience, if the interviewee has no experience.
        - Pick the first and last question from the dataframe among questions fulfilling fit_as_first or fit_as_last.
        - Remove these questions from the dataframe, and decrease the corresponding types self.nbr_x_questions with one.
        - Create a random order for the intermediate questions with the remaining types.
        - For each type in the generated order, retreive a corresponding question from all questions that fulfill the criterion, and remove it from the dataframe.
    When generating each question, one of self.n_alternatives alternatives is chosen randomly.

    Parameters:
        job     (str): Job type of the interview
        no_exp  (bool): Indicates if the interviewee has any previous job experience

    Example question:
        question = {
                "question": "Varför har du sökt det här jobbet?",
                "label": "tough",
                "transition": "Om vi nu funderar på vad som motiverar dig.",
            }
    '''
    def get_interview_questions(self, job, no_exp=False) -> List[Dict[str, str]]:
        '''Returns list of dicts with keys question, label, transition'''

        # Remove irrelevant questions
        self.question_df = self.question_df[(self.question_df.loc[:,'job']==job) | (self.question_df.loc[:,'job']=="Allmän")]
        if no_exp:
            self.question_df = self.question_df[self.question_df.loc[:,'fit_4_no_exp']==True]

        # We only need to return a list of question strings
        question_list = []

        # Append the first question
        question_list.append(self.get_first_question(random.randint(1,self.n_alternatives)))

        # Generate the last question
        last_question = self.get_last_question(random.randint(1,self.n_alternatives))

        # Create a random order of remaining question types
        question_order = []
        for _ in range(self.nbr_always_questions):
            question_order.append("always")
        for _ in range(self.nbr_personal_questions):
            question_order.append("personal")
        for _ in range(self.nbr_job_questions):
            question_order.append("job")
        for _ in range(self.nbr_random_questions):
            question_order.append("random")
        random.shuffle(question_order)
        
        # Append intermediate questions
        for question_type in question_order:
            question_list.append(self.get_intermediate_question(random.randint(1,self.n_alternatives), question_type))

        # Append the last question
        question_list.append(last_question)

        return question_list
    
    '''
    Retrieve the first question in the conversation
    '''
    def get_first_question(self, alt_id) -> Dict[str,str]:
        temp_df = self.question_df[self.question_df.loc[:,'fit_as_first']==1]
        return self.get_random_question_from_df(temp_df, alt_id)

    '''
    Retreive an intermediate question of a specific type
    '''
    def get_intermediate_question(self, alt_id, type) -> Dict[str,str]:
        if type=="always":
            temp_df = self.question_df[self.question_df.loc[:,'always']==1]
        elif type=="personal":
            temp_df = self.question_df[self.question_df.loc[:,'personal']==1]
        elif type=="job":
            temp_df = self.question_df[self.question_df.loc[:,'job']!="Allmän"]
        else: # type==random
            temp_df = self.question_df.copy()
        return self.get_random_question_from_df(temp_df, alt_id)
    
    '''
    Retrieve the last question in the conversation
    '''
    def get_last_question(self, alt_id) -> Dict[str,str]:
        temp_df = self.question_df[self.question_df.loc[:,'fit_as_last']==1]
        # Make sure two random questions are not taken if only one is allowed
        if self.nbr_random_questions==0 and self.nbr_personal_questions>0:
            temp_df = temp_df[temp_df.personal==1]
        return self.get_random_question_from_df(temp_df, alt_id)
    
    '''
    Retreive a random question from a dataframe formatted
    '''
    def get_random_question_from_df(self, temp_df, alt_id) -> Dict[str,str]:
        rand_idx = random.randint(0,temp_df.shape[0]-1)
        question_row = temp_df.iloc[rand_idx,:]
        label = self.get_label(question_row)
        self.discard_question(question_row.question_id)
        return {
            "question": question_row.loc[f"alt_{str(alt_id)}"],
            "label": label,
            "transition": question_row.loc["transition"]
        }

    '''
    Retreive the appropriate label for a specific question
    '''
    def get_label(self, question_row) -> str:
        if question_row.loc["always"]==1:
            self.nbr_always_questions -= 1
            return "general"
        elif question_row.loc["personal"]==1:
            self.nbr_personal_questions -= 1
            return "personal"
        elif question_row.loc["job"]!="Allmän":
            self.nbr_job_questions -= 1
            return "job"
        elif question_row.loc["tough"]==1:
            self.nbr_random_questions -= 1
            return "tough"
        else:
            self.nbr_random_questions -= 1
            return "general"
    
    '''
    Removes the question from the dataframe
    '''
    def discard_question(self, question_id):
        self.question_df = self.question_df[self.question_df.question_id != question_id]

# Example generation
if __name__ == "__main__":
    qg = QuestionGenerator()
    qlist = qg.get_interview_questions("Snickare")
    ii = 1
    for question in qlist:
        if ii==1:
            print(question["question"])
        else:
            print(question["transition"], question["question"])
        print(question["label"])
        print("")
        ii += 1