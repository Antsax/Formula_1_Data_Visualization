import pandas as pd
import os

from pathlib import Path

def get_dataframe(directory, data_set):
    path_to_df = Path(Path.cwd(), directory, data_set)
    return pd.read_csv(path_to_df)

def get_dataframes_from_directory(directory):
    try:
        dataframes = {}
        path_to_directory = Path(Path.cwd(), directory)
        for item in os.listdir(path_to_directory):
            if item.endswith('.csv'):
                dataframes[item.split('.')[0]] = get_dataframe(directory, item)
        return dataframes
    except Exception:
        print(f'Something went wrong. Did you specify the correct path? {path_to_directory}')
