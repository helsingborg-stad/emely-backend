FROM python:3.7
ENV PYTHONUNBUFFERED 1
EXPOSE 4000
COPY ./requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . .


CMD ["uvicorn", "src.api.api_main:brain", "--host", "0.0.0.0"]