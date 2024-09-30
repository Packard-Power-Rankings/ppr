import pandas as pd


def clean_data(df):
    """
    Cleans and normalizes the data from the uploaded CSV file.
    :param df: DataFrame containing the raw data.
    :return: Cleaned and normalized DataFrame.
    """
    # Ensure scores are numeric and fill missing values with 0
    df['home_score'] = pd.to_numeric(
        df['home_score'], errors='coerce').fillna(0).astype(int)
    df['away_score'] = pd.to_numeric(
        df['away_score'], errors='coerce').fillna(0).astype(int)

    # Clean team names: Ensure no missing values
    df['home_team'] = df['home_team'].fillna("Unknown Team")
    df['away_team'] = df['away_team'].fillna("Unknown Team")

    # Clean date: Ensure it's in a valid date format
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    # Handle missing or invalid dates (drop or fill in with a default date)
    df = df.dropna(subset=['date'])  # Drop rows with invalid dates

    # Ensure neutral site field is binary (0 or 1)
    df['neutral_site'] = df['neutral_site'].apply(lambda x: 1 if x == 1 else 0)

    return df
