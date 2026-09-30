# import pytest
# import pandas as pd
# from data_cleaning import clean_data


# def test_clean_data_valid_data():
#     # Create a valid DataFrame
#     df = pd.DataFrame({
#         'date': ['2023-11-19', '2023-11-20'],
#         'home_team': ['Team A', 'Team B'],
#         'away_team': ['Team C', 'Team D'],
#         'home_score': [100, 95],
#         'away_score': [90, 85],
#         'neutral_site': [0, 1]
#     })
#     cleaned_df = clean_data(df)

#     # Assert that the cleaned DataFrame matches the input
#     assert cleaned_df['home_score'].tolist() == [100, 95]
#     assert cleaned_df['away_score'].tolist() == [90, 85]
#     assert cleaned_df['home_team'].tolist() == ['Team A', 'Team B']
#     assert cleaned_df['away_team'].tolist() == ['Team C', 'Team D']
#     assert cleaned_df['date'].notnull().all()


# def test_clean_data_invalid_scores():
#     # Create a DataFrame with invalid scores
#     df = pd.DataFrame({
#         'date': ['2023-11-19', '2023-11-20'],
#         'home_team': ['Team A', 'Team B'],
#         'away_team': ['Team C', 'Team D'],
#         'home_score': ['invalid', '95'],
#         'away_score': [90, 'invalid'],
#         'neutral_site': [0, 1]
#     })
#     cleaned_df = clean_data(df)

#     # Assert that invalid scores are replaced with 0
#     assert cleaned_df['home_score'].tolist() == [0, 95]
#     assert cleaned_df['away_score'].tolist() == [90, 0]


# def test_clean_data_missing_team_names():
#     # Create a DataFrame with missing team names
#     df = pd.DataFrame({
#         'date': ['2023-11-19', '2023-11-20'],
#         'home_team': [None, 'Team B'],
#         'away_team': ['Team C', None],
#         'home_score': [100, 95],
#         'away_score': [90, 85],
#         'neutral_site': [0, 1]
#     })
#     cleaned_df = clean_data(df)

#     # Assert that missing team names are replaced with "Unknown Team"
#     assert cleaned_df['home_team'].tolist() == ['Unknown Team', 'Team B']
#     assert cleaned_df['away_team'].tolist() == ['Team C', 'Unknown Team']


# def test_clean_data_invalid_dates():
#     # Create a DataFrame with invalid dates
#     df = pd.DataFrame({
#         'date': ['2023-11-19', 'invalid_date'],
#         'home_team': ['Team A', 'Team B'],
#         'away_team': ['Team C', 'Team D'],
#         'home_score': [100, 95],
#         'away_score': [90, 85],
#         'neutral_site': [0, 1]
#     })
#     cleaned_df = clean_data(df)

#     # Assert that rows with invalid dates are dropped
#     assert len(cleaned_df) == 2
#     assert cleaned_df['date'].tolist() == [pd.Timestamp('2023-11-19')]


# def test_clean_data_empty_dataframe():
#     # Create an empty DataFrame
#     df = pd.DataFrame(columns=[
#                       'date', 'home_team', 'away_team', 'home_score', 'away_score', 'neutral_site'])
#     cleaned_df = clean_data(df)

#     # Assert that the cleaned DataFrame is still empty
#     assert cleaned_df.empty
#     assert list(cleaned_df.columns) == [
#         'date', 'home_team', 'away_team', 'home_score', 'away_score', 'neutral_site']
