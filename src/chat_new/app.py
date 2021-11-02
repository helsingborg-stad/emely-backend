from fastapi import FastAPI, Response, status, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn
from data import ConversationInit, UserMessage, Message
from worlds import DialogWorld


logging.basicConfig(level=logging.NOTSET)
app = FastAPI()
origins = [
    "http://localhost:3000",
    "https://emely-react-develop-em7jnms6va-lz.a.run.app",
    "https://emely-react-main-em7jnms6va-ey.a.run.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

world = DialogWorld()


async def startup():
    "Run on startup. Currently used to wake models"
    world.wake_models()
    return


app.add_event_handler("startup", startup)


@app.post("/init", status_code=201)
async def new_chat(msg: ConversationInit, response: Response, request: Request):
    persona = msg.persona
    if persona == "intervju" or persona == "fika":
        return await world.create_new_conversation(msg)
    else:
        pass


@app.post("/intervju", status_code=200)
async def interview(user_message: UserMessage, response: Response):
    try:
        reply = await world.interview_reply(user_message)
        return reply
    except Exception as e:
        logging.warning(e)
        response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        return response


@app.post("/fika", status_code=200)
async def fika(user_message: UserMessage, response: Response):
    try:
        reply = await world.fika_reply(user_message)
        return reply
    except Exception as e:
        logging.warning(e)
        response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        return response


if __name__ == "__main__":
    uvicorn.run(app, log_level="warning")

