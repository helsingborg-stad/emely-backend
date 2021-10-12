Emely
==============================

## Pushing and continuous deployment

This repo has CD set up with GCP. GCP will automatically deploy from the develop branch.
To prevent unintended things from happening we add a git hook that's checked before pushing to GitHub.

You'll have to place it in .git/hooks/ manually and you'll find it in the OneDrive under AI ML PROJECTS\Emely\Design - Development - Test\pre-push

Note: If the confirmation doesn't appear for you, please check that you have a git version higher than 1.8.2 (run git --version on the command line) and also check that the pre-push file is executable (run chmod +x pre-push on the command line) and try again :)


## Get started - first time
1. Create and activate the environment in Anaconda prompt
2. Go to root folder and '$ pip install -r requirements' & '$ pip install -e'.
3. Aquire 'emelybrainapi-33194bec3069.json' from OneDrive and put in root-folder.

## Running the brain app locally
To run the fastAPI app on 127.0.0.1:8000
1. Make sure the environment is activated.
2. Go to src/api and run the command '$ uvicorn api_main:brain' 
3. Check the swagger docs and try the http requests at 127.0.0.1:8000/docs



<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
