This is a step by step instruction for how to run the formatting after editing the data from Otter. In order to format
the data correctly for the next step, please read the Data transcription - Instructions for using Otter.
Once this process is finnished, automatic configuration of the data will be run in a series of scripts. After these steps
have been taken, a single text file with all the interactions has been created. This text file may then be used to train
the model using the ParlAI interface.

Step 1. Run the script src/data/rull_all_editing.py
        Aligns the tags (emely or user) with the corresponding text so that there is not a linebreak after the tag.
Step 2. Manually add episode_start and episode_stop of the edited files, where it is appropriate. The only requirement is that
Step 3. Run the script src/data/read_dialouge_data.
        Extract the conversations to .json files. This should be placed in data/json/ and the input text-files should be
        in data/raw/. But it is possible to use some other structure. Remember that the .json files are assigned a random
        name, so that if the script is run multiple times, multiple copies of the same conversation might be created.
        It is possible to remove all .json files the in output_directory.
Step 4. Run the script src/data/json_to_parlai.py
        This creates a .txt-file with all the conversation on the format that is requried by ParlAI.


