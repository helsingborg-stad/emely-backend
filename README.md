Emely
==============================
## Overview
This project was developed by NordAxon for Helsingborg Stad 2021-2022, and open sourced in April 2023.

Emely is a Conversational AI System for practicing job interviews in Swedish. The dialogue model is a finetuned Blenderbot 1.

The project is separated in 3 repositories: [emely-frontend](https://github.com/helsingborg-stad/emely-frontend), [emely-backend](https://github.com/helsingborg-stad/emely-backend) & [emely-models](https://github.com/helsingborg-stad/emely-models).

## Deployment & Environment variables
The project is built around deployment using Google Cloud Platform, using Cloud Run, Cloud Build, Firebase Authentication & Firestore. 
The deployment code is set up for Cloud Build, and assumes that environment variables are stored as substitution variables in a Cloud Build Trigger.


## Get started - first time
1. Create and activate the environment in Anaconda prompt
2. Install dependencies and module
```
    $ pip install -r requirements.txt
    $ python setup.py develop
```
3. Create, or get existing json credentials for a GCP service account with role _Firebase Admin SDK Administrator Service Agent_ and put in root-folder.

## Running the server on localhost
```$uvicorn app:app --reload```

Check the swagger docs and try the http requests at localhost:8000/docs


## Adding things to Emely's filter

There's a "lie filter" with sentences that Emely isn't allowed to say. 

To add things to this list, edit the list "lies" in chat/dialog/filters.py

