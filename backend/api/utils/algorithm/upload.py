import pandas as pd


def upload_csv(file_path):
    """
    Function to upload and validate a CSV file.
    :param file_path: Path to the CSV file to be uploaded.
    :return: DataFrame containing the uploaded and validated data.
    """
    try:
        # Load the CSV file and assign column names manually
        column_names = ["date", "home_team", "away_team",
                        "home_score", "away_score", "neutral_site"]
        df = pd.read_csv(file_path, header=None, names=column_names)

        # Check if the required columns are present
        required_columns = ["date", "home_team", "away_team",
                            "home_score", "away_score", "neutral_site"]
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")

        # Return the validated DataFrame
        return df

    except Exception as e:
        print(f"Error loading CSV file: {e}")
        return None
