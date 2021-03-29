from google.cloud import storage
from pathlib import Path
import os

def download_model_dir(model, dl_dir, bucket):
    blobs = bucket.list_blobs(prefix=model)  # Get list of files

    model_dir = dl_dir / model / 'model'
    token_dir = dl_dir / model / 'tokenizer'
    model_dir.mkdir(parents=True, exist_ok=True)
    token_dir.mkdir(parents=True, exist_ok=True)
    for blob in blobs:
        filename = blob.name
        blob.download_to_filename(dl_dir / filename)  # Download

def download_models(model_dirs: list):
    bucket_name = 'emelys_models'
    project_dir = Path(__file__).resolve().parents[2]
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = project_dir.joinpath('emelybrainapi-7fe03b6e672c.json').as_posix()

    dl_dir = project_dir / 'models'

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    for model_dir in model_dirs:
        download_model_dir(model_dir, dl_dir, bucket)
