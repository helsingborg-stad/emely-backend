import logging
import requests
from data import UserMessage
from typing import Dict
import os
import aiohttp
from utils import timer

interview_model_url = "https://interview-model-ef5bmjer3q-ey.a.run.app"
fika_model_url = "https://blender-90m-ef5bmjer3q-ey.a.run.app"
rasa_nlu_url = "https://rasa-nlu-ef5bmjer3q-ey.a.run.app"


class MLModel:
    """Parent class for all models
    """

    def __init__(self, url):
        self.url = url

    def get_response(self, x):
        ""
        inputs = self._format_input(x)
        r = requests.post(url=self.url, json=inputs)
        outputs = self._format_outputs(r)

        return outputs

    def _format_input(self, x):
        raise NotImplementedError(
            "Override and implement this function in your MLModel subclass!"
        )

    def _format_outputs(self, y):
        raise NotImplementedError(
            "Override and implement this function in your MLModel subclass"
        )

    def wake_up(self):
        "Sends a request with a short timeout to wake up gcp instance"
        try:
            requests.get(url=self.model_url, timeout=0.01)
        except:
            logging.info(f"Sent wake up call to {type(self)} model")


class HuggingfaceFika(MLModel):
    pass


class InterviewModel(MLModel):
    "Interfaces communication with the interview model"

    def __init__(self, url=interview_model_url):
        inference_url = url + "/inference"
        super().__init__(url=inference_url)

    def _format_input(self, x):
        return {"text": x}

    def _format_outputs(self, y):
        t = y.elapsed
        y = y.json()
        time = t.seconds + t.microseconds / 1000000

        return (y["text"], time)


class FikaModel(InterviewModel):
    "Interfaces communication with the Fika model"

    def __init__(self, url=fika_model_url):
        super().__init__(url=url)


class RasaModel(MLModel):
    "Interfaces communication with the Rasa NLU model"

    def __init__(self):
        self.model_url = rasa_nlu_url
        self.inference_url = self.model_url + "/model/parse"
        self.dummy_reponse = {"id": "", "name": "", "confidence": 0}
        self.enabled = os.environ.get("RASA_ENABLED", "0")

    async def get_response(self, user_message: UserMessage) -> Dict:
        "Calls rasa model for NLU classification"
        if not self.enabled:
            return self.dummy_reponse

        if user_message.lang == "sv":
            text = user_message.text
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url=self.inference_url, json={"text": text}, timeout=0.5
                    ) as resp:
                        r = await resp.json()
                return r["intent"]
            except Exception as e:
                print(e)
                return self.dummy_reponse
        else:
            return self.dummy_reponse

