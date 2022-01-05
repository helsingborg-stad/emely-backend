from fastapi import FastAPI, Response, status, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn
from chat.data.types import ConversationInit, UserMessage, Message
from chat.dialog.worlds import DialogWorld


logging.basicConfig(level=logging.NOTSET)
app = FastAPI()
origins = [
    "http://localhost:3000",
    "https://emely-react-develop-em7jnms6va-lz.a.run.app",
    "https://emely-react-main-em7jnms6va-ey.a.run.app",
    "https://emely-react-main-west1-em7jnms6va-ew.a.run.app",
    "https://emely-develop.nordaxon.com",
    "https://emely.nordaxon.com",
    "https://emely-demo.nordaxon.com",
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
    reply = await world.interview_reply(user_message)
    return reply


@app.post("/fika", status_code=200)
async def fika(user_message: UserMessage, response: Response):
    reply = await world.fika_reply(user_message)
    return reply


@app.get("/joblist")
def get_joblist():
    return {"occupations": world.question_generator.get_job_list()}


@app.get("/user_conversations")
def get_user_conversations(user_id: str):
    return {
        "user_conversations": world.database_handler.get_user_conversations_formatted(
            user_id
        )
    }


if __name__ == "__main__":
    uvicorn.run(app, log_level="warning")

