FROM tiangolo/uvicorn-gunicorn-fastapi:latest
ENV PYTHONUNBUFFERED 1

COPY ./ /app
WORKDIR /app

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -e .
RUN python -c "import nltk; nltk.download('punkt')"

ARG huggingface_key
ARG use_huggingface_fika
ENV PORT 8080
ENV HUGGINGFACE_KEY=$huggingface_key
ENV USE_HUGGINGFACE_FIKA=$use_huggingface_fika
# Set environment variables to change behaviour of backend

