from pathlib import Path

import pandas as pd


SUPPORTED_EXTENSIONS = {".csv", ".xlsx"}


class FileService:
    @staticmethod
    def load_file(file_path):
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix not in SUPPORTED_EXTENSIONS:
            raise ValueError("Please select a CSV or XLSX file.")

        if suffix == ".csv":
            dataframe = pd.read_csv(path)
        else:
            dataframe = pd.read_excel(path)

        return dataframe.fillna("")

    @staticmethod
    def save_file(dataframe, file_path):
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix == ".csv":
            dataframe.to_csv(path, index=False)
            return

        if suffix == ".xlsx":
            dataframe.to_excel(path, index=False)
            return

        raise ValueError("Please save the file as CSV or XLSX.")
