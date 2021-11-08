FROM python:3.9
ENV PYTHONUNBUFFERED 1

COPY ./ ./
ENV PORT 8080

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -e .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]