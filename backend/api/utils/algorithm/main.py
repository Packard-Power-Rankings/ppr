from typing import List
import numpy as np  # For numerical operations
import pandas as pd


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


def calculate_expected_performance(expected):
    """
    Calculate expected performance based on the power difference.
    :param df: DataFrame containing enriched data.
    :return: DataFrame with expected performance added.
    """
    return ((expected + 2.0) ** 0.45) - (2.0 ** 0.45)


def calculate_actual_performance(actual):
    """
    Calculate the actual performance based on the modified score differences.
    Convert the result to a boolean (1 for positive, 0 for negative).
    :param df: DataFrame containing enriched data.
    :return: DataFrame with actual performance added as boolean.
    """
    if actual >= 0:
        return ((actual + 2.0) ** 0.45) - (2.0 ** 0.45) + 1.0
    return -1.0 * ((-1.0 * actual + 2.0) ** 0.45 - (2.0 ** 0.45)) - 1.0


def power_change(actual_performance, expected_performance, k_value):
    return (actual_performance - expected_performance) * k_value


def calculate_power_difference(df):
    """
    Calculate the power difference between home and away teams.
    :param df: DataFrame containing enriched data.
    :return: DataFrame with power difference added.
    """
    def power_differences(row):
        if row['expected_home_wl'] >= 0:
            expected_home_performance = \
                calculate_expected_performance(row['expected_home_wl'])
            expected_visitor_performance = \
                expected_home_performance * -1.0
        else:
            expected_visitor_performance = \
                calculate_expected_performance(row['expected_away_wl'])
            expected_home_performance = \
                expected_visitor_performance * -1.0

        actual_home_wl = row['modified_home_score'] - row['modified_away_score']
        actual_away_wl = row['modified_away_score'] - row['modified_home_score']

        actual_home_performance = \
            calculate_actual_performance(actual_home_wl)
        actual_away_performance = \
            calculate_actual_performance(actual_away_wl)
        home_power_change = \
            power_change(
                actual_home_performance,
                expected_home_performance,
                row['k_value']
            )
        away_power_change = \
            power_change(
                actual_away_performance,
                expected_visitor_performance,
                row['k_value']
            )
        row['home_team_power_ranking'] += home_power_change
        row['away_team_power_ranking'] += away_power_change

        return pd.Series(
            [
                row['home_team_power_ranking'],
                row['away_team_power_ranking'],
                home_power_change,
                away_power_change,
            ]
        )
    df[
        [
            'home_team_power_ranking',
            'away_team_power_ranking',
            'home_power_change',
            'away_power_change',
        ]
    ] = df.apply(power_differences, axis=1)
    return df


def expected_wl(df):
    def calculate_expected_wl(row):
        expected_home_wl = (
            row['home_team_power_ranking'] - row['away_team_power_ranking'] +
            row['home_field_advantage']
        )
        expected_away_wl = (
            row['away_team_power_ranking'] - row['home_team_power_ranking'] +
            (-1.0 * row['home_field_advantage'])
        )
        return pd.Series([expected_home_wl, expected_away_wl])
    df[['expected_home_wl', 'expected_away_wl']] = \
        df.apply(calculate_expected_wl, axis=1)
    return df


def modify_game_scores(df):
    """
    Modify the game scores based on the power rankings and average game score.
    :param df: DataFrame containing enriched data.
    :return: DataFrame with modified game scores.
    """
    def modified_scores(row):
        # Calculate score modification logic
        if row['home_score'] - row['away_score'] >= 0:
            modified_home_score = (
                10.0 * row['AVEGAMESC'] + 9.0 * row['home_score']
                - 10.0 * row['away_score']
            ) / 19.0
            modified_away_score = row['AVEGAMESC'] - modified_home_score
            mov = row['home_score'] - row['away_score']
            mov_mod = modified_home_score - modified_away_score
            if row['home_score'] + row['away_score'] == 0:
                mov_mod1 = -9E10
            else:
                mov_mod1 = (
                    50.0 / (row['home_score'] + row['away_score'])
                ) * mov
            mov_mod2 = max(mov_mod, mov_mod1)
            if row['home_score'] + row['away_score'] < row['AVEGAMESC']:
                mov_mod2 = mov_mod
            modified_home_score = round(25.0 + 0.5 * mov_mod2, 5)
            modified_away_score = round(50 - modified_home_score, 5)
        else:
            modified_away_score = (
                10.0 * row['AVEGAMESC'] + 9.0 * row['away_score']
                - 10.0 * row['home_score']
            ) / 19.0
            modified_home_score = row['AVEGAMESC'] - modified_away_score
            mov = row['away_score'] - row['home_score']
            mov_mod = modified_away_score - modified_home_score
            mov_mod1 = (
                50.0 / (row['home_score'] + row['away_score'])
            ) * mov
            mov_mod2 = max(mov_mod, mov_mod1)
            if row['home_score'] + row['away_score'] < row['AVEGAMESC']:
                mov_mod2 = mov_mod
            modified_away_score = round(25.0 + 0.5 * mov_mod2, 5)
            modified_home_score = round(50.0 - modified_away_score, 5)

        return pd.Series([modified_home_score, modified_away_score])

    df[['modified_home_score', 'modified_away_score']] = \
        df.apply(modified_scores, axis=1)
    return df


def process_team_data(
    teams_id_dict,
    recent_opponents,
    actual_power_change
):
    temp_loop_change = 0.0

    for i in range(1, 6):
            if recent_opponents[i] == 0:
                continue
            depth1 = teams_id_dict[recent_opponents[i]]
            for k in range(0, 6):
                if k >= 5 or depth1['recent_opp'][k] == 0:
                    continue
                depth2 = teams_id_dict[depth1['recent_opp'][k]]
                if k == 0:
                    depth2['power_ranking'][-1] += \
                        (1.0/3.0) * ((0.5)**(i-1 + k)) * actual_power_change
                    temp_loop_change += \
                        (1.0/3.0) * ((0.5)**(i-1 + k)) * actual_power_change
                    continue
                for m in range(0, 6):
                    if m >= 5 or depth2['recent_opp'][m] == 0:
                        continue
                    depth3 = teams_id_dict[depth2['recent_opp'][m]]
                    if m == 0:
                        depth3['power_ranking'][-1] += \
                            (1.0/3.0) * ((0.5)**(i-1 + k + m)) * actual_power_change
                        temp_loop_change += \
                            (1.0/3.0) * ((0.5)**(i-1 + k + m)) * actual_power_change
                        continue
                    for l in range(0, 6):
                        if l >= 5 or depth3['recent_opp'][l] == 0:
                            continue
                        depth4 = teams_id_dict[depth3['recent_opp'][l]]
                        if l == 0:
                            depth4['power_ranking'][-1] += \
                                (1.0/3.0) * ((0.5)**(i-1 + k + m + l)) * actual_power_change
                            temp_loop_change += \
                                (1.0/3.0) * ((0.5)**(i-1 + k + m + l)) * actual_power_change
                            continue
                        for q in range(0, 6):
                            if q >= 5 or depth4['recent_opp'][q] == 0:
                                continue
                            depth5 = teams_id_dict[depth4['recent_opp'][q]]
                            depth5['power_ranking'][-1] += \
                                (1.0/3.0) * ((0.5)**(i-1 + k + m + l + q)) * actual_power_change
                            temp_loop_change += \
                                (1.0/3.0) * ((0.5)**(i-1 + k + m + l + q)) * actual_power_change


def update_recent_opp_list(opp_list: List, team_num):
    opp_list.pop()
    opp_list.pop(0)
    opp_list.insert(0, team_num)
    return opp_list


def nested_power_change(df, teams_id_dict, teams_names_dict):
    def calculate_power_change(row):
        home_team = teams_names_dict[row['home_team'].lower()]
        home_opponent_ids = home_team['recent_opp']
        home_opponent_ids.insert(0, home_team['team_id'])

        home_team['power_ranking'][-1] += row['home_power_change']

        away_team = teams_names_dict[row['away_team'].lower()]
        away_opponent_ids = away_team['recent_opp']
        away_opponent_ids.insert(0, away_team['team_id'])
        
        away_team['power_ranking'][-1] += row['away_power_change']

        process_team_data(
            teams_id_dict,
            home_opponent_ids,
            row['home_power_change']
        )

        process_team_data(
            teams_id_dict,
            away_opponent_ids,
            row['away_power_change']
        )

        home_opponent_ids = update_recent_opp_list(
            home_opponent_ids,
            away_team['team_id']
        )
        away_opponent_ids = update_recent_opp_list(
            away_opponent_ids,
            home_team['team_id']
        )

    df.apply(calculate_power_change, axis=1)


def set_adjusted_power_rankings(df, teams_names_dict):
    def power_rankings_change(row):
        updated_home_pr = \
            teams_names_dict[row['home_team'].lower()]['power_ranking'][-1]
        updated_away_pr = \
            teams_names_dict[row['away_team'].lower()]['power_ranking'][-1]
        return pd.Series([updated_home_pr, updated_away_pr])
    df[['home_team_power_ranking', 'away_team_power_ranking']] = \
        df.apply(power_rankings_change, axis=1)
    return df


def run_calculations(df, teams_data):
    """
    Run all the calculations for the algorithm.
    :param df: DataFrame containing enriched data.
    :return: Final DataFrame with all calculations done.
    """
    teams_id_dict = {
        team_id["team_id"]: team_id for team_id in teams_data
    }
    teams_names_dict = {
        team_name["team_name"].lower(): team_name for team_name in teams_data
    }
    df = modify_game_scores(df)
    df = expected_wl(df)
    df = calculate_power_difference(df)
    nested_power_change(df, teams_id_dict, teams_names_dict)
    # df = set_adjusted_power_rankings(df, teams_names_dict)

    df = calculate_z_scores(df)
    return df, teams_data
