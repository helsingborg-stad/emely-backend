from pathlib import Path
from typing import List, Dict

import random

class QuestionGenerator:

    def __init__(self, nbr_questions = 2):
        self.nbr_questions = nbr_questions
        self.competence_questions = ["Om du ska jobba som {0} är det bra om du har erfarenhet av {1}. Kan du beskriva din erfarenhet inom detta område?",
                  "I din roll som {0} måste du kunna någonting om {1}. Kan du berätta om dina kunskaper om {1}?",
                  "För tjänsten som {0} har vi tänkt att du ska jobba med {1}. Hur känner du inför det?",
                  ]

        self.non_competence_questions = ['Vad gör att du skulle passa bra som {}?',
                                  'Vad är din bästa erfarenhet från dina tidigare arbeten?',  
                                  'Är det någonting som du vill fråga om det här arbetet?']

        self.job_to_competences = parse_data(Path('core_competences.txt'))
        self.job_list = self.job_to_competences.keys()


    def get_interview_questions(self, job:str) -> List:
        """ Called by InterviewConversation to generate questions""" 

        if job in self.job_list:
            return self.get_competence_questions(job)

        else:
            return self.get_general_questions(job)


    def get_general_questions(self, job:str) -> List:
        """ Used for jobs we haven't seen in the data collection """
        questions = ['Du har sökt job som {}. Vad är det som du tycker verkar vara roligt med detta arbete?',
                    'Om du ska arbeta som {} så är det bra om du har erfarenhet från att jobba tillsammans med andra. Kan du berätta lite om du har sådan erfarenhet?',
                    'Och vad gör att du skulle passa bra som {}?',
                    'Vad är din bästa erfarenhet från dina tidigare arbeten?',
                    'Är det någonting som du vill fråga om det här arbetet?']
        formatted_questions = [q.format(job) if '{}' in q else q for q in questions]
        return formatted_questions


    def get_competence_questions(self, job:str) -> List:
        """ Used if the job is NOT in the list of supported jobs that data was collected for"""
        nbr_questions = self.nbr_questions
        job_competences = self.job_to_competences[job]
        competences = random.sample(job_competences, nbr_questions)
        questions = random.sample(self.competence_questions, nbr_questions)

        formatted_questions = []
        for i in range(nbr_questions):
            competence_question = questions[i].format(job, competences[i])
            formatted_questions.append(competence_question)

        formatted_questions.append(self.non_competence_questions[0].format(job))
        formatted_questions.append(self.non_competence_questions[1])
        formatted_questions.append(self.non_competence_questions[2])

        return formatted_questions


def parse_data(p:Path) -> Dict:
    """ Reads the competence data from file and returns a dictionary of job -> list of competences"""
    
    with open(p, 'r', encoding="UTF-8") as f:
        data = f.read()
        datalines = data.split('\n')
        
    job_to_competences = {}
    for line in datalines:
        job, competences = line.split(':')
        competences = competences.split(';')
        for i in range(len(competences)):
            c = competences[i].strip(' ').strip(';').lower()
            competences[i] = c
        
        job_to_competences[job] = competences[:-1]
            
    return job_to_competences
