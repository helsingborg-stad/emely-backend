from chat.data.types import Conversation, BotMessage, UserMessage
import re
from itertools import product
from difflib import SequenceMatcher
from typing import Tuple, List
from chat.hardcoded_messages.badwords import badwords
import os

lies = [
    "do you have any hobbies?",
    "i'm a stay at home mom",
    "i'm unemployed",
    "i'm just about to start my interview",
    "thank you for your time",
    "it's not a good way to live",
    "that's not a good way to live",
    "hope you are fine with your dad in bed",
    "dad is fine in bed",
    "i have children with my child",
]
min_text_length = 4


def contains_toxicity(user_message: UserMessage) -> bool:
    """ Checks if any swedish badword is in the message """
    if user_message.lang == "sv":
        sentence = user_message.text.lower()
        offensive = any([bad_word in sentence for bad_word in badwords])
        return offensive

    else:
        return False


def is_too_repetitive(bot_message: BotMessage, conversation: Conversation) -> bool:
    """Modifies bot_message.text if it contains parts that are repetitive. 
    Will return True if it is too heavily modified and too little text is left.

    Args:
        conversation (Conversation): [description]
        bot_message (BotMessage): [description]

    Returns:
        bool: True if text is pruned
    """

    # We only filter if it's an english utterance from the blenderbot
    if bot_message.lang != "en":
        return False

    else:
        # What if we have a really long conversation? Is it okay to only check the latest X messages? Computation time can be a "problem" if we have a 40 message conversation
        previous_replies = conversation.get_emely_messages(
            int(os.environ["N_MESSAGES_FOR_REPETITION_FILTER"])
        )
        if len(previous_replies) == 0:
            return False

        sentences, separators = split_text_into_sentences(bot_message.text)

        # Split the previous sentences into
        previous_sentences = []
        for text in previous_replies:
            text_parts, _ = split_text_into_sentences(text)
            previous_sentences.extend(text_parts)

        similarity_threshold = float(os.environ["SIMILARITY_THRESHOLD"])
        keep_idx = []
        # We loop over the sentences in bot_message and check how similar they are to previous sentences
        # idx is appended to keep_idx if the sentence is deemed okay to keep
        for i in range(len(sentences)):
            combos = list(product([sentences[i]], previous_sentences))
            ratios = [SequenceMatcher(a=s1, b=s2).ratio() for s1, s2 in combos]
            if max(ratios) < similarity_threshold:
                keep_idx.append(i)

        # Everything is kept
        if len(keep_idx) == len(sentences):
            return False
        # Everything is removed
        elif len(keep_idx) == 0:
            return True

        # Stitch together sentence
        keep_sentences = [sentences[i] for i in keep_idx]
        keep_separators = [separators[i] for i in keep_idx]
        new_reply = stitch_together_sentences(keep_sentences, keep_separators)

        # Last check if it's too short
        if len(new_reply) > min_text_length:
            bot_message.text = new_reply
            return False
        else:
            return True


def remove_lies(bot_message: BotMessage) -> bool:
    "Removes lies (in english) "

    # We don't do anything if message is in english, there are no lies or the filter is deactivated
    if bot_message.lang != "en" and len(lies) != 0 and not os.environ["LIE_FILTER"]:
        return False

    sentences, separators = split_text_into_sentences(bot_message.text)

    lie_threshold = float(os.environ["LIE_THRESHOLD"])

    keep_idx = []
    # Create combinations of sentences and lies and check if they are similar
    for i in range(len(sentences)):
        combos = list(product([sentences[i]], lies))
        lie_probabilities = [SequenceMatcher(a=s1, b=s2).ratio() for s1, s2 in combos]
        if max(lie_probabilities) < lie_threshold:
            keep_idx.append(i)

    keep_sentences = [sentences[i] for i in keep_idx]
    keep_separators = [separators[i] for i in keep_idx]

    # Everything is kept
    if len(keep_idx) == len(sentences):
        return False
    # Everything is removed
    elif len(keep_idx) == 0:
        return True

    new_reply = stitch_together_sentences(keep_sentences, keep_separators)

    # Last check if it's too short
    if len(new_reply) > min_text_length:
        bot_message.text = new_reply
        return False
    else:
        return True


# Method 2: Just remove if


def split_text_into_sentences(text: str) -> Tuple[List[str], List[str]]:
    "Helper func. Splits a text on . ? and ! and returns a list with the sentences and the separators"

    sentence_parts = re.split("([.?!])", text)
    if sentence_parts[-1] == "":
        del sentence_parts[-1]

    # We split the sentence parts into the words and the .?! signs
    sentences = [sep for i, sep in enumerate(sentence_parts) if i % 2 == 0]
    separators = [sep for i, sep in enumerate(sentence_parts) if i % 2 != 0]

    return (sentences, separators)


def stitch_together_sentences(sentences: List[str], separators: List[str]) -> str:
    "Helper func. Stitches together a list of sentence and separators into a string of sentences"
    stitched_text = ""

    for i in range(len(sentences)):
        try:
            stitched_text = stitched_text + sentences[i] + separators[i] + " "

        # If the original text didn't end with a separator we can get an IndexError
        except IndexError:
            stitched_text = stitched_text + sentences[i]

    return stitched_text

