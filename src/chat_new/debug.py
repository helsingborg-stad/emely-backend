from data import ConversationInit, Conversation, UserMessage, Message
from worlds import InterviewWorld
import asyncio
import time

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
    "job": "Snickare",
    "has_experience": True,
    "enable_small_talk": False,
    "user_id": "123456",
}

msg = {
    "created_at": "1999-01-01 00:00:00.000000",
    "lang": "sv",
    "text": "Hej Emely jag har jobbat i många många år men jag är fortfarande inte redo för att ta en chefsposition",
    "recording_used": False,
    "response_time": 0.0,
}

msgs = [
    "Hej Emely jag har jobbat i många många år men jag är fortfarande inte redo för att ta en chefsposition",
    "jag älskar att hjälpa människor",
    "nej jag har inte jobbat med det innan",
    "är det viktigt att jag kommer i tid?",
]

if __name__ == "__main__":

    world = InterviewWorld()

    conversation_init = ConversationInit(**init)

    first_reply = asyncio.run(world.create_new_conversation(conversation_init))
    user_msg = UserMessage(**msg, conversation_id=first_reply.conversation_id)

    t1 = time.time()
    for i in range(2):
        msg["text"] = msgs[i]
        user_msg = UserMessage(**msg, conversation_id=first_reply.conversation_id)
        reply = asyncio.run(world.respond(user_msg))
    t2 = time.time()
    print(t2 - t1)