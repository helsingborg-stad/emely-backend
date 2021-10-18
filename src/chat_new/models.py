import requests

interview_model_url = "https://interview-model-ef5bmjer3q-ey.a.run.app"
fika_model_url = "https://blender-90m-ef5bmjer3q-ey.a.run.app"


class MLModel:
    """Parent class for all models
    """

    def __init__(self, url):
        self.url = url

    def get_response(self, x):
        assert self._check_input(x)
        inputs = self._format_input(x)
        r = requests.post(url=self.url, json=inputs)
        outputs = self._format_outputs(r)

        return outputs

    def _check_input(self, x):
        # TODO: Implement. x should follow blenderbot format or just be a plain string if it's rasa
        return True

    def _format_input(self, x):
        raise NotImplementedError(
            "Override and implement this function in your MLModel subclass!"
        )

    def _format_outputs(self, y):
        raise NotImplementedError(
            "Override and implement this function in your MLModel subclass"
        )

    def wake_up(self):
        "Sends a dummy request to wake up GCP instance"
        # TODO: ASync wake up call
        pass


class HuggingfaceFika(MLModel):
    pass


class InterviewModel(MLModel):
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
    def __init__(self, url=fika_model_url):
        super().__init__(url=url)


class RasaModel(MLModel):
    pass
