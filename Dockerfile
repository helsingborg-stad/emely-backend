FROM python:3.7
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /requirements.txt
ENV PORT 8080

RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p models/blenderbot_small-90M@f70_v2_acc20/model
RUN mkdir -p models/blenderbot_small-90M@f70_v2_acc20/tokenizer
RUN mkdir -p models/blenderbot_small-90M/model
RUN mkdir -p models/blenderbot_small-90M/tokenizer
RUN git describe > git_build.txt

COPY ./src /src

CMD ["uvicorn", "src.api.api_main:brain", "--host", "0.0.0.0", "--port", "8080"]