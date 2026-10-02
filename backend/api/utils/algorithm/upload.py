import pandas as pd

from api.service.game_ingestion import GAME_COLUMNS, parse_game_csv


def upload_csv(file_path):
    """
    Function to upload and validate a CSV file.
    :param file_path: Path to the CSV file to be uploaded.
    :return: DataFrame containing the uploaded and validated data.
    """
    try:
        if hasattr(file_path, "read"):
            file_content = file_path.read()
        else:
            with open(file_path, "rb") as game_file:
                file_content = game_file.read()
        games = parse_game_csv(file_content)
        return pd.DataFrame(
            [game.as_dict() for game in games],
            columns=GAME_COLUMNS,
        )
    except FileNotFoundError:
        print(f"Error loading CSV file: File not found: {file_path}")
        return None
