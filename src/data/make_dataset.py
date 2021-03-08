# -*- coding: utf-8 -*-
import click
import logging
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split


def read_interview_files(input_filepath: Path, output_filepath: Path):
    # TODO: Read files
    # TODO: Split episode on episode_done
    # TODO: Identify how many follow up questions is in an episode, and how many samples it can produce
    # TODO: Split into X,Y, remove 'freja:' and 'user:' and add special tokens

    # TODO: Read one or several files
    id = 0
    files = [file for file in input_filepath.iterdir() if file.suffix == '.txt']
    texts = []
    for file in files:
        with open(file, 'r') as f:
            texts.append(f.read())

    src_target_dict = {}
    for text in texts:
        # TODO: Split every text into episodes
        episodes = text.split('episode_done')
        for episode in episodes:
            # Count how many _follow up questions_ freja asks
            lines = episode.split('\n')
            lines = list(filter(('').__ne__, lines))
            # Remove unwanted empty lines
            nbr_follow_up_questions = sum([1 for line in lines if 'freja' in line]) - 1

            # We get rid of 'freja: ' and 'user: ' in the lines
            new_lines = []
            for line in lines:
                line = line.replace('freja:', '')
                line = line.replace('user:', '')
                new_lines.append(line)
            for i in range(2, nbr_follow_up_questions * 2 + 1, 2):
                target = new_lines[i]
                src = ''
                for j in range(i):
                    src = src + new_lines[j] + '\n'

                sample_id = str(id).zfill(6)
                src_target_dict[sample_id] = {'src': src, 'target': target}
                id += 1
    # Convert to DataFrame and split into test and validation sets
    src_target_df = pd.DataFrame.from_dict(src_target_dict, orient='index')

    train_df, val_df = train_test_split(src_target_df, test_size=0.20, shuffle=True)

    train_csv_path = output_filepath.joinpath('interview_train.csv')
    val_csv_path = output_filepath.joinpath('interview_val.csv')
    train_df.to_csv(train_csv_path, index_label='Name')
    val_df.to_csv(val_csv_path, index_label='Name')
    return



def main(input_filepath, output_filepath):
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """
    logger = logging.getLogger(__name__)
    logger.info('making final data set from raw data')
    data_path = project_dir.joinpath('data')
    raw_data_path = project_dir.joinpath(input_filepath)
    processed_data_path = project_dir.joinpath(output_filepath)
    if not data_path.exists():
        data_path.mkdir()
    if not raw_data_path.exists():
        raw_data_path.mkdir()
    if not processed_data_path.exists():
        processed_data_path.mkdir()

    read_interview_files(raw_data_path,processed_data_path)

if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables

    main(input_filepath='data/raw', output_filepath='data/processed')
