import pandas as pd


def upload_csv(file_path):
    """
    Function to upload and validate a CSV file.
    :param file_path: Path to the CSV file to be uploaded.
    :return: DataFrame containing the uploaded and validated data.
    """
    try:
        # Load the CSV file
        column_names = ["date", "home_team", "away_team",
                        "home_score", "away_score", "neutral_site"]
        df = pd.read_csv(file_path, header=None)

        # Handle empty file
        if df.empty:
            return pd.DataFrame(columns=column_names)

        # Validate column count
        if len(df.columns) != len(column_names):
            raise ValueError(
                "CSV does not contain the correct number of columns.")

        # Assign column names
        df.columns = column_names

        # Check if the required columns are present
        for col in column_names:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")

        # Return the validated DataFrame
        return df

    except FileNotFoundError:
        print(f"Error loading CSV file: File not found: {file_path}")
        return None
    except pd.errors.EmptyDataError:
        print("Error loading CSV file: No columns to parse from file.")
        return pd.DataFrame(columns=["date", "home_team", "away_team", "home_score", "away_score", "neutral_site"])
    except Exception as e:
        raise e  # Re-raise exceptions for validation errors
