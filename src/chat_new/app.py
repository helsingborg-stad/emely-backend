from fastapi import FastAPI, Response, status, Request
import logging
import uvicorn
from data import ConversationInit, UserMessage, Message
from worlds import InterviewWorld

app = FastAPI()
logging.basicConfig(level=logging.NOTSET)


interview_world = InterviewWorld()
# fika_world = FikaWorld()


async def startup():
    "Run on startup. Currently used to wake models"
    interview_world.wake_models()
    # fika_world.wake_models()
    return


app.add_event_handler("startup", startup)


@app.post("/init", status_code=201)
async def new_chat(msg: ConversationInit, response: Response, request: Request):
    if msg.persona == "intervju":
        return interview_world.create_new_conversation(msg)
    elif msg.persona == "fika":
        pass
    else:
        pass


@app.post("/intervju", status_code=200)
async def interview(msg: UserMessage, response: Response):
    pass


@app.post("/fika", status_code=200)
async def fika(msg: UserMessage, response: Response):
    pass


if __name__ == "__main__":
    uvicorn.run(app, log_level="warning")

