import pandas as pd

def read_file(path):
    if path.endswith(".csv"):
        return pd.read_csv(path)
    return pd.read_excel(path)

def save_file(df, path):
    df.to_excel(path, index=False)