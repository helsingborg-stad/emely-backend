import requests_async as requests
import asyncio
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

"""
This is a test for response time when simulating multiple chatters. (Currently only tests fika)

Used to find out how gunicorn with uvicorn workers affect latency.

It produces a scatterplot with elapsed time(y) and message number(x) and the hue(conversation_id) indicates which simulated chatter it was.
Also prints mean elapsed time for all messages and by conversation_id


The test works like this:
1. X conversations are initiated
2. Loop over number of messages
    - each time, send a battery of messages(one for each conversation) to the backend
    - gather all results and note elapsed times
3. Produce plot and means

"""


# --------------- parameters ------------------
url = "https://emely-backend-develop-em7jnms6va-ey.a.run.app"

nbr_messages = 5
nbr_chatters = 4


# ---------------------------------------------


init_url = url + "/init"
fika_url = url + "/fika"


dummy_data = {
    "created_at": "1999-01-01 00:00:00.000000",
    "conversation_id": "ZX6r7gN8yC9b3eS97ZEG",
    "lang": "sv",
    "text": "Hej Emely hur är det med du",
    "recording_used": False,
    "response_time": 0,
}

init_data = {
    "created_at": "1999-04-07 18:59:24.584658",
    "development_testing": True,
    "lang": "sv",
    "name": "testing testing",
    "persona": "fika",
    "user_ip_number": "127.0.0.1",
    "job": "Snickare",
    "has_experience": True,
    "enable_small_talk": True,
    "user_id": None,
}


async def create_convo():
    r = await requests.post(init_url, json=init_data)

    conversation_id = r.json()["conversation_id"]
    return conversation_id


async def dummy_request(conversation_id):
    data = dummy_data
    data["conversation_id"] = conversation_id
    r = await requests.post(fika_url, json=data)
    return r


if __name__ == "__main__":

    loop = asyncio.get_event_loop()

    init_tasks = asyncio.gather(*[create_convo() for i in range(nbr_chatters)])
    conversation_ids = loop.run_until_complete(init_tasks)
    print(conversation_ids)

    # We send a request per conversation_id to the backend and then gather them
    elapsed = []
    for i in range(nbr_messages):

        tasks = asyncio.gather(*[dummy_request(c) for c in conversation_ids])

        responses = loop.run_until_complete(tasks)
        for r in responses:
            elapsed.append(
                {
                    "conversation_id": r.json()["conversation_id"],
                    "elapsed": r.elapsed.total_seconds(),
                    "message": i,
                }
            )

    loop.close()
    df = pd.DataFrame(elapsed)
    print("Total mean", df["elapsed"].mean())
    print("Means by conversation id")
    print(df.groupby("conversation_id").mean())

    plt.figure()
    sns.scatterplot(x="message", y="elapsed", data=df, hue="conversation_id")
    plt.show()
