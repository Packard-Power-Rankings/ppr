import os
import pandas as pd


def save_to_csv(df, output_path):
    """
    Save the processed DataFrame to a CSV file.
    :param df: DataFrame to be saved.
    :param output_path: Path where the file will be saved.
    """
    try:
        # Check if the file already exists
        if os.path.exists(output_path):
            print(
                f"File {output_path} already exists. It will not be overwritten.")
            return

        # Create directories if they do not exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Save the file
        df.to_csv(output_path, index=False)
        print(f"File saved to {output_path}.")
    except Exception as e:
        raise ValueError(f"Error saving to {output_path}: {e}")
