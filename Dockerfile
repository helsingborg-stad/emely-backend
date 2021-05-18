FROM python:3.7
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /requirements.txt
ENV PORT 8080

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
COPY ./git_version.txt /git_version.txt

COPY ./src /src

CMD ["uvicorn", "src.api.api_main:brain", "--host", "0.0.0.0", "--port", "8080"]