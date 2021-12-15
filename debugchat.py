from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# -------------------PARAMS---------------------
persona = "intervju"
conversation_id = None  # Set to none to start a new one
job = "Allmän intervjuträning"

# ----------------------------------------

init_data = {
    "created_at": "1999-04-07 18:59:24.584658",
    "development_testing": True,
    "lang": "sv",
    "name": "swaggerdocs",
    "persona": persona,
    "user_ip_number": "127.0.0.1",
    "job": "Snickare",
    "has_experience": True,
    "enable_small_talk": False,
    "user_id": None,
    "use_huggingface": False,
}

if conversation_id is None:
    r = client.post("/init", json=init_data).json()
    conversation_id = r["conversation_id"]
data = {
    "created_at": "1999-01-01 00:00:00.000000",
    "conversation_id": conversation_id,
    "lang": "sv",
    "text": "fuck kuk",
    "recording_used": False,
    "response_time": 0,
}

while True:
    d = data
    m = input(">>> ")
    d["text"] = m
    print("User: ", m)
    if persona == "fika":
        r = client.post("/fika", json=d)
    elif persona == "intervju":
        r = client.post("/intervju", json=d)
    print("Emely: ", r.json()["text"])
