Emely
==============================

## Pushing and continuous deployment

This repo has CD set up with GCP. GCP will automatically deploy from the develop branch.
To prevent unintended things from happening we add a git hook that's checked before pushing to GitHub.

You'll have to place it in .git/hooks/ manually and you'll find it in the OneDrive under AI ML PROJECTS\Emely\Design - Development - Test\pre-push

Note: If the confirmation doesn't appear for you, please check that you have a git version higher than 1.8.2 (run git --version on the command line) and also check that the pre-push file is executable (run chmod +x pre-push on the command line) and try again :)


## Get started - first time
1. create a new virtual environment
2. pip install -e .

## Running the brain app locally
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


--------

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
