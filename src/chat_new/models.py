import requests


class MLModel:
    """Parent class for all models
    """

    def __init__(self, url):
        self.url = "http://"

    def get_response(self, x):
        inputs = self._format_input(x)
        r = requests.post(url=self.url, json=inputs)
        outputs = self._format_outputs(r)

        return r

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


class HuggingfaceFika(MLModel):
    pass


class InterviewModel(MLModel):
    pass


class RasaModel(MLModel):
    pass
