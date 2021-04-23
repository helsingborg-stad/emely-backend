from argparse import ArgumentParser
from sklearn.model_selection import train_test_split
from pathlib import Path
import re


def split_parlai_in_episodes(text):
    episodes = text.split('episode_done:True\n')
    new_episodes = []
    for i, episode in enumerate(episodes):
        if i != len(episodes) - 1:
            episode = episode + 'episode_done:True\n'
            new_episodes.append(episode)
        else:
            if episode == '\n' or episode == '':
                print('last episode split was a newline, good')
            else:
                raise ValueError('Formatting problem at the end of the file?')

    return new_episodes


def episode_to_parlai(episodes):
    """ Stitches list of episodes together to one string of parlai format"""
    parlai_text = ''
    for episode in episodes:
        parlai_text = parlai_text + episode

    return parlai_text


def create_datasets(episodes):
    """ Splits data set twice into 90%, 9%, 1% """
    train_episodes, other_episodes = train_test_split(episodes, train_size=0.9, test_size=0.1)
    val_episodes, test_episodes = train_test_split(other_episodes, train_size=0.9, test_size=0.1)

    train_text = episode_to_parlai(train_episodes)
    val_text = episode_to_parlai(val_episodes)
    test_text = episode_to_parlai(test_episodes)

    return train_text, val_text, test_text


def main(files, dataset_name):
    project_dir = Path(__file__).resolve().parents[2]
    data_dir = project_dir / 'data/parlai'
    assert data_dir.exists()

    file_paths = []
    for file in files:
        f = Path(file)
        if f.suffix == '.txt':
            path_to_file = data_dir / file
        elif f.suffix == '':
            path_to_file = data_dir / (file + '.txt')
        else:
            msg = 'File contained suffix {} which is not .txt'.format(f.suffix)
            raise ValueError(msg)

        assert path_to_file.exists(), 'data/parlai/{} did not exist'.format(file)
        file_paths.append(path_to_file)

    all_episodes = []
    for file in file_paths:
        with open(file, 'r') as f:
            text = f.read()

        episodes = split_parlai_in_episodes(text)
        all_episodes.extend(episodes)

    train_set, val_set, test_set = create_datasets(all_episodes)

    dataset_name = Path(dataset_name).name
    dataset_path = data_dir.joinpath(dataset_name)
    dataset_path.mkdir(exist_ok=True, parents=True)
    train_path = dataset_path / 'train.txt'
    val_path = dataset_path / 'valid.txt'
    test_path = dataset_path / 'test.txt'

    # Write them to file
    with open(train_path, 'w') as f:
        f.write(train_set)

    with open(val_path, 'w') as f:
        f.write(val_set)

    with open(test_path, 'w') as f:
        f.write(test_set)


if __name__ == '__main__':
    """ Creates a folder with train/val/test split of a file containing """

    parser = ArgumentParser()
    parser.add_argument('-f', '--files', nargs='+',
                        help='Files in data/parlai to include in the dataset split. Separate with space', required=True)
    parser.add_argument('-d', '--dataset_name', type=str, required=True, help='name of dataset')
    args = parser.parse_args()

    main(args.files, args.dataset_name)
