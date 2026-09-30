import pandas as pd


def upload_csv(file_path, schema=None):
    """
    Load and validate a CSV file.
    :param file_path: Path to the CSV file.
    :param schema: Optional schema to enforce column names.
    :return: DataFrame with the uploaded data.
    """
    try:
        if schema:
            df = pd.read_csv(file_path, header=None, names=schema)
        else:
            df = pd.read_csv(file_path)

        # Validate required columns if a schema is provided
        if schema:
            for col in schema:
                if col not in df.columns:
                    raise ValueError(f"Missing required column: {col}")

        return df

    except Exception as e:
        raise ValueError(f"Error loading CSV file {file_path}: {e}")
