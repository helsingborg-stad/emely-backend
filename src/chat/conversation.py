from pathlib import Path
from collections import deque


class OpenConversation:

    def __init__(self, name, tokenizer):
        self.name = name
        self.conversation_sv = BlenderConversation(lang='sv', tokenizer=tokenizer)
        self.conversation_en = BlenderConversation(lang='en', tokenizer=tokenizer)
        self.episode_done = False
        self.tokenizer = tokenizer
        self.persona = 'your persona: my name is Emely'
        self.persona_length = len(self.tokenizer(self.persona)['input_ids'])

    def one_step_back(self):
        self.conversation_sv.pop()
        self.conversation_sv.pop()
        self.conversation_en.pop()
        self.conversation_en.pop()
        return self.conversation_sv.bot_text[-1]

    def reset_conversation(self):
        self.conversation_sv.reset()
        self.conversation_en.reset()
        return

    def get_context(self):
        context = '{}\n{}'.format(self.persona, self.conversation_en.get_dialogue_history(30))
        return context


class InterviewConversation:

    def __init__(self, name, job, tokenizer):
        self.name = name
        self.job = job.lower()
        self.conversation_sv = BlenderConversation(lang='sv', tokenizer=tokenizer)
        self.conversation_en = BlenderConversation(lang='en', tokenizer=tokenizer)
        self.nbr_replies = 0
        self.last_input_is_question = False
        self.episode_done = False
        self.questions = [question.format(self.job) if format_this else question for (question, format_this) in
                          read_questions((Path(__file__).parent / 'interview_questions.txt'))]
        self.tokenizer = tokenizer
        self.persona = 'your persona: My name is Emely and I am an AI interviewer'
        self.persona_length = len(self.tokenizer(self.persona)['input_ids'])

    def one_step_back(self):
        self.conversation_sv.pop()
        self.conversation_sv.pop()
        self.conversation_en.pop()
        self.conversation_en.pop()
        self.nbr_replies -= 1
        return self.conversation_sv.bot_text[-1]

    def reset_conversation(self):
        self.conversation_sv.reset()
        self.conversation_en.reset()
        return

    def get_context(self):
        # context = '{}\n{}'.format(self.persona, self.conversation_en.get_dialogue_history(40))
        context = self.conversation_en.get_nbr_interactions(self.nbr_replies)
        return context


class BlenderConversation:

    def __init__(self, lang, tokenizer):
        self.lang = lang
        self.bot_text = []
        self.user_text = []
        self.user_turn = None
        self.tokenizer = tokenizer

    def reset(self):
        self.bot_text = []
        self.user_text = []
        self.user_turn = True

    def add_user_text(self, text):
        if self.user_turn or self.user_turn is None:
            self.user_text.append(text)
            self.user_turn = False
        else:
            raise ValueError("It's the bot's turn to add a reply to the conversation")
        return

    def add_bot_text(self, text):
        if not self.user_turn or self.user_turn is None:
            self.bot_text.append(text)
            self.user_turn = True
        else:
            raise ValueError("It's the user's turn to add an input to the conversation")
        return

    def pop(self):
        if self.user_turn:
            self.bot_text.pop()
            self.user_turn = False
        else:
            self.user_text.pop()
            self.user_turn = True
        return

    def get_bot_replies(self):
        return self.bot_text

    def get_user_replies(self):
        return self.user_text

    def get_dialogue_history(self, max_len=120):
        # Returns string of the dialogue history with bot and user inputs separated with '\n'
        # max_len set to default 100 as model has max input length 128 and we want some space for new input
        history = ''
        tokens_left = max_len
        if self.user_turn:
            # Start backwards from bot_text
            for i in reversed(range(len(self.user_text))):
                bot_text = self.bot_text[i]
                user_text = self.user_text[i]
                nbr_tokens = len(self.tokenizer(bot_text)['input_ids']) + len(self.tokenizer(user_text)['input_ids'])
                if nbr_tokens < tokens_left:  # This is not fool proof as the model tokenizer tokenizes differently
                    history = user_text + '\n' + bot_text + '\n' + history
                    tokens_left -= (nbr_tokens + 2)
                else:
                    break

        else:
            # Start backwards from user_text
            history = self.user_text[-1]
            tokens_left -= len(self.tokenizer(history)['input_ids'])
            for i in reversed(range(len(self.user_text) - 1)):
                bot_text = self.bot_text[i]
                user_text = self.user_text[i]
                nbr_tokens = len(self.tokenizer(bot_text)['input_ids']) + len(self.tokenizer(user_text)['input_ids'])
                if nbr_tokens < tokens_left:
                    history = user_text + '\n' + bot_text + '\n' + history
                    tokens_left -= (nbr_tokens + 2)
                else:
                    break
        return history

    def to_txt(self, description, file, error=None):
        # Writes the dialogue to txt file in subdirectory
        text = '####################################\n' + 'Conversation description: ' + description + '\n\n'
        if self.user_turn:
            for i in range(len(self.user_text)):
                text = text + 'User>>> ' + self.user_text[i] + '\n Bot>>> ' + self.bot_text[i] + '\n'
        else:
            for i in range(len(self.bot_text)):
                text = text + 'User>>> ' + self.user_text[i] + '\n Bot>>> ' + self.bot_text[i] + '\n'
            text = text + 'User>>> ' + self.user_text[-1]

        if error is None:
            text = text + '\n\n'
        else:
            text = text + '\n' + 'Terminated due to {}'.format(error) + '\n\n'

        with open(file, 'a') as f:
            f.write(text)
        return

    def print_dialogue(self):
        # Prints the dialogue
        text = ''
        if self.user_turn:
            for i in range(len(self.user_text)):
                text = text + 'User>>> ' + self.user_text[i] + '\n Bot>>> ' + self.bot_text[i] + '\n'
        else:
            for i in range(len(self.bot_text)):
                text = text + 'User>>> ' + self.user_text[i] + '\n Bot>>> ' + self.bot_text[i] + '\n'
            text = text + 'User>>> ' + self.user_text[-1]

            print(text)
        return

    def get_nbr_interactions(self, nbr):
        """Retrieves only the last nbr interactions in the conversation as a string formatted with \n separators"""
        lines = deque()
        assert not self.user_turn  # Needs to be bots turn for this method to be used
        for i in range(nbr + 1):
            backindex = -1 - i
            lines.appendleft(self.user_text[backindex])
            lines.appendleft(self.bot_text[backindex])
        context = ''
        for line in lines:
            context = context + line + '\n'
        context = context.rsplit('\n', 1)[0]
        return context


def read_questions(file_path):
    # Reads interview questions from a text file, one question per line. '{}' in place where job should be inserted
    with open(file_path, 'r') as f:
        questions = f.readlines()
    format_this = [True if '{}' in question else False for question in questions]
    return zip(questions, format_this)
