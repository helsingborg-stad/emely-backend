from data import ConversationInit, Conversation, UserMessage, Message
from worlds import InterviewWorld

init = {
    "brain_url": "null",
    "created_at": "debugg time",
    "development_testing": True,
    "lang": "sv",
    "name": "Max DeBugg",
    "persona": "intervju",
    "user_ip_number": "127.0.0.1",
    "webapp_local": True,
    "webapp_url": "null",
    "webapp_version": "null",
    "job": "debugger",
    "has_experience": True,
    "enable_small_talk": True,
    "user_id": "123456",
}

msg = {
    "created_at": "1999-01-01 00:00:00.000000",
    "lang": "sv",
    "text": "Hej Emely",
    "recording_used": False,
    "response_time": 0.0,
}

question_list = [
    {"question": "Varför har du sökt det här jobbet?", "label": "tough"},
    {"question": "Hur är du som person?", "label": "personal"},
]

current_dialog_block = "tough"

conversation_id = "0UNFqtlc73ya8oLCb9LJ"


def test():
    conversation_init = ConversationInit(**init)

    c1 = Conversation(
        current_dialog_block=current_dialog_block,
        conversation_id=conversation_id,
        episode_done=False,
        question_list=question_list,
        brain_url="a",
        job="test",
        name="test",
        user_id="test",
        user_ip_number="test",
        webapp_url="test",
        webapp_version="test",
        lang="test",
        created_at="test",
        development_testing=True,
        persona="test",
        webapp_local=True,
    )

    c2 = Conversation(
        **dict(conversation_init),
        current_dialog_block=current_dialog_block,
        conversation_id=conversation_id,
        episode_done=False,
        question_list=question_list,
    )
    return c2


if __name__ == "__main__":

    world = InterviewWorld()

    conversation_init = ConversationInit(**init)

    first_reply = world.create_new_conversation(conversation_init)
    user_msg = UserMessage(**msg, conversation_id=first_reply.conversation_id)

    for i in range(5):
        reply = world.respond(user_msg)

