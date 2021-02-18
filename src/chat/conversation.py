from pathlib import Path

class BlenderConversation:

    def __init__(self, lang, tokenizer):
        self.lang = lang
        self.bot_text = []
        self.user_text = []
        self.user_turn = True
        self.tokenizer = tokenizer

    def reset(self):
        self.bot_text = []
        self.user_text = []
        self.user_turn = True

    def add_user_text(self, text):
        if self.user_turn:
            self.user_text.append(text)
            self.user_turn = False
        else:
            raise ValueError("It's the bot's turn to add a reply to the conversation")
        return

    def add_bot_text(self, text):
        if not self.user_turn:
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
        # TODO: Option to return string instead of list?
        return self.bot_text

    def get_user_replies(self):
        # TODO: Option to return string instead of list?
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
                if nbr_tokens < tokens_left:  # This is not fool proof as the model tokenizer tokenizes differently
                    history = user_text + '\n' + bot_text + '\n' + history
                    tokens_left -= (nbr_tokens + 2)
                else:
                    break
        return history

    def to_txt(self, description, file=None,  error=None):
        # Writes the dialogue to txt file in subdirectory
        text = '####################################\n' + 'Conversation description: ' + description + '\n\n'
        if self.user_turn:
            for i in range(len(self.user_text)):
                text = text + 'User>>> ' + self.user_text[i] + '\n Bot>>> ' + self.bot_text[i] + '\n'
        else:
            for i in range(len(self.bot_text)):
                text = text + 'User>>> ' + self.user_text[i] + '\n Bot>>> ' + self.bot_text[i] + '\n'
            text = text + 'User>>> ' + self.user_text[-1]

        if file is None:
            if self.lang == 'sv':
                file = 'interview_sv.txt'
            else:
                file = 'interview_en.txt'


        if error is None:
            text = text + '\n\n'
        else:
            text = text + '\n' + 'Terminated due to {}'.format(error) + '\n\n'
        file_path = file
        with open(file_path, 'a') as f:
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
