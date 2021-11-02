FROM python:3.7
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /requirements.txt
ENV PORT 8080

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src /src

WORKDIR /src/chat_new/

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]