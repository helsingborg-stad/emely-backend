Emely
==============================

## Pushing and continuous deployment

This repo has CD set up with GCP. GCP will automatically deploy from the develop branch.
To prevent unintended things from happening we add a git hook that's checked before pushing to GitHub.

You'll have to place it in .git/hooks/ manually and you'll find it in the OneDrive under AI ML PROJECTS\Emely\Design - Development - Test\pre-push

Note: If the confirmation doesn't appear for you, please check that you have a git version higher than 1.8.2 (run git --version on the command line) and also check that the pre-push file is executable (run chmod +x pre-push on the command line) and try again :)


## Get started - first time
1. Create and activate the environment in Anaconda prompt
2. Install dependencies and module
```
    $ pip install -r requirements.txt
    $ python setup.py develop
```
3. Aquire 'emelybrainapi-33194bec3069.json' from OneDrive and put in root-folder.

## Running the server on localhost
```$uvicorn app:app --reload```

Check the swagger docs and try the http requests at localhost:8000/docs


## Adding things to Emely's filter

There's a "lie filter" with sentences that Emely isn't allowed to say. 

To add things to this list, edit the list "lies" in chat/dialog/filters.py

