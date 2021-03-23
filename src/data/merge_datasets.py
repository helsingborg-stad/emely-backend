from pathlib import Path
from argparse import ArgumentParser
import pandas as pd


def clean_dataframe(df: pd.DataFrame):
    """ Removes short only numeric examples as they are unintelligent"""

    for index, row in df.iterrows():
        target = row['target']
        length = len(target)
        numeric = target.strip(' ').isdecimal()
        if numeric or length < 7:
            df.drop(index=index, inplace=True)
    return df


def main(args):
    data_path = Path(__file__).resolve().parents[2] / 'data/processed'
    csv1_path = data_path / args.csv1
    csv2_path = data_path / args.csv2
    new_df_path = data_path / args.new_name

    df1 = pd.read_csv(csv1_path)
    df2 = pd.read_csv(csv2_path)

    df1 = clean_dataframe(df1)
    df2 = clean_dataframe(df2)
    print('length of df1 is: ', len(df1))
    print('length of df2 is: ', len(df2))

    new_df = pd.concat([df1, df2], ignore_index=True)
    print('length of new_df is: ', len(new_df))
    new_df.to_csv(new_df_path)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--csv1', type=str, required=True)
    parser.add_argument('--csv2', type=str, required=True)
    parser.add_argument('--new_name', type=str, required=True)
    args = parser.parse_args()
    main(args)
