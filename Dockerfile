FROM python:3.9
ENV PYTHONUNBUFFERED 1

COPY ./ ./

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -e .


ENV PORT 8080
ENV HUGGINGFACE_KEY=$HUGGINGFACE_KEY
ENV USE_HUGGINGFACE_FIKA=$USE_HUGGINGFACE_FIKA
# Set environment variables to change behaviour of backend



CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]