Emely
==============================

## Get started - first time
1. create a new virtual environment
2. pip install -e .

## Running the brain app
To run the fastAPI app on 127.0.0.1:8000
1. from src/api $uvicorn api_main:brain 
2. Check the docs and try the http requests at 127.0.0.1:8000/docs



Project Organization
------------

    ├── LICENSE
    ├── README.md          <- The top-level README for developers using this project.
    ├── data
    │   ├── json           <- Intermediate data that has been transformed.
    │   ├── processed      <- The final, canonical data sets for modeling.
    │   └── raw            <- The original, immutable data dump.
    │
    ├── docs               <- Eventual documentation files
    │
    ├── models             <- Storage of blenderbot models and tokenizers
    │
    ├── requirements.txt   <- The requirements file for reproducing the analysis environment
    │
    ├── setup.py           <- makes project pip installable (pip install -e .) so src can be imported
    ├── src                <- Source code for use in this project.
    │   ├── __init__.py    <- Makes src a Python module
    │   │
    │   ├── api            <- Code related to the api and hosting the brain backend
    │   │
    │   ├── chat           <- Code used to handle conversations with Emely
    │   │
    │   ├── data           <- Scripts to process data
    │   │


--------

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
