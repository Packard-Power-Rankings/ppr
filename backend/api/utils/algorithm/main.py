import numpy as np  # For numerical operations


def calculate_power_difference(df):
    """
    Calculate the power difference between home and away teams.
    :param df: DataFrame containing enriched data.
    :return: DataFrame with power difference added.
    """
    df['power_difference'] = abs(
        df['home_team_power_ranking'] - df['away_team_power_ranking'])
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
    Calculate expected performance based on win/loss ratios.
    :param df: DataFrame containing enriched data.
    :return: DataFrame with expected performance added.
    """
    df['expected_performance_home'] = df['home_team_win_ratio'] * \
        df['home_team_power_ranking']
    df['expected_performance_away'] = df['away_team_win_ratio'] * \
        df['away_team_power_ranking']
    return df


def calculate_actual_performance(df):
    """
    Compare the actual game result with the expected performance.
    :param df: DataFrame containing enriched data.
    :return: DataFrame with actual performance metrics.
    """
    df['actual_performance_home'] = np.where(
        df['home_score'] > df['away_score'], 1, 0)  # 1 for win, 0 for loss
    df['actual_performance_away'] = np.where(
        df['away_score'] > df['home_score'], 1, 0)
    return df


def predict_scores(df):
    """
    Predict the final scores based on power difference, home field advantage, 
    and other factors.
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
    df = calculate_z_scores(df)
    df = calculate_expected_performance(df)
    df = calculate_actual_performance(df)
    df = predict_scores(df)

    return df
