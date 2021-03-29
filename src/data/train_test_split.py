from sklearn.model_selection import train_test_split
from argparse import ArgumentParser
from pathlib import Path
import pandas as pd


def main(data_file):
    project_dir = Path(__file__).resolve().parents[2]
    data_file = Path(data_file)
    csv = project_dir / 'data/processed' / data_file
    data = pd.read_csv(csv)

    train, test = train_test_split(data, test_size=0.1)
    assert len(train) > len(test)

    train_path = project_dir / 'data/processed' / (str(data_file.stem) + '_train.csv')
    test_path = project_dir / 'data/processed' / (str(data_file.stem) + '_test.csv')
    train.to_csv(train_path)
    test.to_csv(test_path)



if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--data_file', type=str, required=True)
    args = parser.parse_args()
    main(args.data_file)