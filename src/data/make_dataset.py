# -*- coding: utf-8 -*-
import click
import logging
from pathlib import Path
import pandas as pd
from argparse import ArgumentParser


def read_interview_files(input_filepath: Path, output_filepath: Path):
    index = 0
    with open(input_filepath, 'r') as f:
        text = f.read()

    src_target_dict = {}
    episodes = text.split('episode_done')
    for episode in episodes:
        # Count how many _follow up questions_ freja asks
        lines = episode.split('\n')
        lines = list(filter(('').__ne__, lines))
        if len(lines)==0:
            continue

        # Remove unwanted empty lines
        #nbr_follow_up_questions = sum([1 for line in lines if 'freja' in line]) - 1

        # Make sure episode ends with freja/emelys question so we can set it as target
        if 'freja' not in lines[-1]:
            lines.pop(-1)
            assert 'freja' in lines[-1], 'Something strange is going on'

        # We get rid of 'freja: ' and 'user: ' in the lines,  remove eventual first space and capitalize
        formatted_lines = []
        for line in lines:
            line = line.replace('freja:', '')
            line = line.replace('user:', '')
            if line[0] == ' ':
                line = line[1:]
            line = line.capitalize()
            formatted_lines.append(line)

        target = formatted_lines[-1]
        src = ''
        for i in range(len(formatted_lines)-1):
            src = src + '\n' + formatted_lines[i]

        sample_id = str(index).zfill(6)
        src_target_dict[sample_id] = {'src': src, 'target': target}
        index += 1

    src_target_df = pd.DataFrame.from_dict(src_target_dict, orient='index')

    # Check for empty rows and remove them
    src_target_df = src_target_df[(src_target_df['target'] != '')]
    src_target_df = src_target_df[(src_target_df['src'] != '')]

    out_file = project_dir / 'data/processed' / output_filepath

    src_target_df.to_csv(out_file, index_label='Name')
    return


def main(input_filepath, output_filepath):
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """
    input_file = project_dir / 'data/raw' / input_filepath
    output_file = project_dir / 'data/processed' / output_filepath

    read_interview_files(input_file, output_file)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--input_file', type=str, required=True)
    parser.add_argument('--output_file', type=str, required=True)
    args = parser.parse_args()

    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables

    main(input_filepath=args.input_file, output_filepath=args.output_file)
