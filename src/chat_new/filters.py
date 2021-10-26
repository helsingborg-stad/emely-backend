from data import Conversation, BotMessage
import re
from itertools import product
from difflib import SequenceMatcher

lies = ["i'm a stay at home mom"]
similarity_threshold = 0.9
min_text_length = 10


def contains_toxicity(message) -> bool:
    # TODO: Implement
    return False


def is_to_repetitive(bot_message: BotMessage, conversation: Conversation) -> bool:
    """Modifies bot_message.text if it contains parts that are repetitive. 
    Will return True if it is too heavily modified and too little text is left.

    Args:
        conversation (Conversation): [description]
        bot_message (BotMessage): [description]

    Returns:
        bool: True if text is pruned
    """

    # We only filter if it's an english utterance from the blenderbot
    # TODO: is this a good enough condition?
    if bot_message.lang != "en":
        return False

    else:
        # What if we have a really long conversation? Is it okay to only check the latest X messages? Computation time can be a "problem" if we have a 40 message conversation
        previous_replies = conversation.get_all_emely_messages()
        if len(previous_replies) == 0:
            return False

        sentence_parts = re.split("([.?!])", bot_message.text)
        if sentence_parts[-1] == "":
            del sentence_parts[-1]

        # We split the sentence parts into the words and the .?! signs
        sentences = [sep for i, sep in enumerate(sentence_parts) if i % 2 == 0]
        separators = [sep for i, sep in enumerate(sentence_parts) if i % 2 != 0]

        # Split the previous sentences into
        previous_sentences = []
        for text in previous_replies:
            raw_text_parts = re.split("[.?!]", text)
            text_parts = [part for part in raw_text_parts if len(part) > 2]
            previous_sentences.extend(text_parts)

        keep_idx = []
        # We loop over the sentences in bot_message and check how similar they are to previous sentences
        # idx is appended to keep_idx if the sentence is deemed okay to keep
        for i in range(len(sentences)):
            combos = list(product([sentences[i]], previous_sentences))
            ratios = [SequenceMatcher(a=s1, b=s2).ratio() for s1, s2 in combos]
            if max(ratios) < similarity_threshold:
                keep_idx.append(i)

        if len(keep_idx) == len(sentences):
            return False
        elif len(keep_idx) == 0:
            return True

        # Stitch together sentence
        new_reply = ""
        for i in keep_idx:
            try:
                new_reply = new_reply + sentences[i] + separators[i] + " "
            except IndexError:
                new_reply = new_reply + sentences[i]

        # Last check if it's too short
        if len(new_reply) > min_text_length:
            bot_message.text = new_reply
            return False
        else:
            return True

