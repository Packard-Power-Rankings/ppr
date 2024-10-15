import numpy as np  # For numerical operations
import pandas as pd


def calculate_power_difference(df):
    """
    Calculate the power difference between home and away teams.
    :param df: DataFrame containing enriched data.
    :return: DataFrame with power difference added.
    """
    df['power_difference'] = df['home_team_power_ranking'] + \
        df['home_field_advantage'] - df['away_team_power_ranking']
    return df


def calculate_z_scores(df):
    """
    Calculate Z-scores for the home and away teams based on their scores.
    :param df: DataFrame containing enriched data.
    :return: DataFrame with Z-scores for home and away teams.
    """
    all_scores = df['home_score'].tolist() + df['away_score'].tolist()
    mean_score = np.mean(all_scores)
    std_dev_score = np.std(all_scores)

    df['home_z_score'] = (df['home_score'] - mean_score) / \
        std_dev_score if std_dev_score != 0 else 0
    df['away_z_score'] = (df['away_score'] - mean_score) / \
        std_dev_score if std_dev_score != 0 else 0

    return df


def calculate_expected_performance(df):
    """
    Calculate expected performance based on the power difference.
    :param df: DataFrame containing enriched data.
    :return: DataFrame with expected performance added.
    """
    def expected_performance(diff):
        if diff >= 0:
            return ((diff + 2) ** 0.45) - (2 ** 0.45)
        else:
            return -(((abs(diff) + 2) ** 0.45) - (2 ** 0.45))

    df['expected_performance_home'] = df['power_difference'].apply(
        expected_performance)
    df['expected_performance_away'] = df['expected_performance_home'] * - \
        1  # Away team is the inverse
    return df


def modify_game_scores(df):
    """
    Modify the game scores based on the power rankings and average game score.
    :param df: DataFrame containing enriched data.
    :return: DataFrame with modified game scores.
    """
    def modified_scores(row):
        # Calculate score modification logic
        if row['home_team_power_ranking'] >= row['away_team_power_ranking']:
            modified_home_score = (10 * row['AVEGAMESC']
                                   + 9 * row['home_team_power_ranking']
                                   - 10 * row['away_team_power_ranking']) / 19
            modified_away_score = row['AVEGAMESC'] - modified_home_score
        else:
            modified_away_score = (10 * row['AVEGAMESC']
                                   + 9 * row['away_team_power_ranking']
                                   - 10 * row['home_team_power_ranking']) / 19
            modified_home_score = row['AVEGAMESC'] - modified_away_score

        return pd.Series([modified_home_score, modified_away_score])

    df[['modified_home_score', 'modified_away_score']
       ] = df.apply(modified_scores, axis=1)
    return df


def calculate_actual_performance(df):
    """
    Calculate the actual performance based on the modified score differences.
    Convert the result to a boolean (1 for positive, 0 for negative).
    :param df: DataFrame containing enriched data.
    :return: DataFrame with actual performance added as boolean.
    """
    def actual_performance(modmov2):
        if modmov2 >= 0:
            value = ((modmov2 + 2) ** 0.45) - (2 ** 0.45) + 1
        else:
            value = -(((abs(modmov2) + 2) ** 0.45) - (2 ** 0.45)) - 1

        # Convert to boolean: 1 if positive, 0 if negative
        return 1 if value > 0 else 0

    # Calculate margin of victory
    df['MODMOV2_home'] = df['modified_home_score'] - df['modified_away_score']
    df['MODMOV2_away'] = df['modified_away_score'] - df['modified_home_score']

    # Apply actual performance calculation and convert to boolean
    df['actual_performance_home'] = df['MODMOV2_home'].apply(
        actual_performance)
    df['actual_performance_away'] = df['MODMOV2_away'].apply(
        actual_performance)

    return df


def predict_scores(df):
    """
    Predict final scores based on power difference, home field advantage, etc.
    :param df: DataFrame containing enriched data.
    :return: DataFrame with predicted scores added.
    """
    df['predicted_home_score'] = df['home_team_power_ranking'] + \
        df['home_field_advantage']
    # No home field advantage for away team
    df['predicted_away_score'] = df['away_team_power_ranking']
    return df


def run_calculations(df):
    """
    Run all the calculations for the algorithm.
    :param df: DataFrame containing enriched data.
    :return: Final DataFrame with all calculations done.
    """
    df = calculate_power_difference(df)
    df = calculate_z_scores(df)  # Ensure Z-scores are calculated and included
    df = calculate_expected_performance(df)
    df = modify_game_scores(df)  # Modify the game scores
    df = calculate_actual_performance(df)  # Actual performance returns boolean
    df = predict_scores(df)

    return df
