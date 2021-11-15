FROM python:3.9
ENV PYTHONUNBUFFERED 1

COPY ./ ./

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -e .

ARG huggingface_key
ARG use_huggingface_fika
ENV PORT 8080
ENV HUGGINGFACE_KEY=$huggingface_key
ENV USE_HUGGINGFACE_FIKA=$use_huggingface_fika
# Set environment variables to change behaviour of backend



CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]