import pandas as pd


def clean_data(df):
    """
    Clean and normalize game data.
    :param df: DataFrame with raw data.
    :return: Cleaned DataFrame.
    """
    # Standardize column names
    df.columns = ['home_team', 'away_team',
                  'home_score', 'away_score', 'neutral_site']

    # Remove placeholder rows
    df = df[~((df['home_team'] == "XXX") | (df['away_team'] == "XXX"))]
    df = df[~((df['home_score'] == 0) & (df['away_score'] == 0))]

    # Ensure scores are numeric
    df['home_score'] = pd.to_numeric(
        df['home_score'], errors='coerce').fillna(0).astype(int)
    df['away_score'] = pd.to_numeric(
        df['away_score'], errors='coerce').fillna(0).astype(int)

    # Ensure neutral site is binary
    df['neutral_site'] = df['neutral_site'].apply(
        lambda x: 1 if x == 999 else 0)

    return df
