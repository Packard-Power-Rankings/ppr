import numpy as np  # For numerical operations
import pandas as pd
from typing import Tuple, Dict, Any, List
# from config.config import CONSTANTS_MAP
from config.team_state import TeamState


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
    return ((expected + 2.0) ** 0.45) - (2 ** 0.45)


def calculate_actual_performance(actual):
    """
    Calculate the actual performance based on the modified score differences.
    Convert the result to a boolean (1 for positive, 0 for negative).
    :param df: DataFrame containing enriched data.
    :return: DataFrame with actual performance added as boolean.
    """
    if actual >= 0:
        return ((actual + 2.0) ** 0.45) - (2.0 ** 0.45) + 1.0
    else:
        return -1.0 * ((-1.0 * actual + 2.0) ** 0.45 - (2.0 ** 0.45)) - 1


def power_change(actual_performance, expected_performance, r_value):
    return r_value * (actual_performance - expected_performance)


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
        actual_visitor_performance = \
            calculate_actual_performance(actual_away_wl)
        home_power_change = \
            power_change(
                actual_home_performance,
                expected_home_performance,
                row['R_value']
            )
        away_power_change = \
            power_change(
                actual_visitor_performance,
                expected_visitor_performance,
                row['R_value']
            )
        row['home_team_power_ranking'] += home_power_change
        row['away_team_power_ranking'] += away_power_change

        return pd.Series(
            [
                row['home_team_power_ranking'],
                row['away_team_power_ranking'],
                home_power_change,
                away_power_change
            ]
        )
    df[
        [
            'home_team_power_ranking',
            'away_team_power_ranking',
            'home_power_change',
            'away_power_change'
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
                50.0 / (row['away_score'] + row['home_score'])
            ) * mov
            mov_mod2 = max(mov_mod, mov_mod1)
            if row['away_score'] + row['home_score'] < row['AVEGAMESC']:
                mov_mod2 = mov_mod
            modified_away_score = round(25.0 + 0.5 * mov_mod2, 5)
            modified_home_score = round(50.0 - modified_away_score, 5)

        return pd.Series([modified_home_score, modified_away_score])

    df[['modified_home_score', 'modified_away_score']] = \
        df.apply(modified_scores, axis=1)
    return df


def update_team_power_ranking(team, team_power_change, depth_factor):
    team['power_ranking'] = \
        team.get('power_ranking', 0) + team_power_change * depth_factor


def process_team_opponents(
    team_info: Dict,
    recent_opp: List,
    team_power_change: float,
    depth: int,
    max_depth: int,
    depth_factor: float
):
    if depth > max_depth:
        return
    for team_id in recent_opp:
        if team_id == 0:
            continue
        team = team_info.get(team_id)
        update_team_power_ranking(team, team_power_change, depth_factor)
        process_team_opponents(
            team_info,
            team_info[team_id].get('recent_opp'),
            team_power_change,
            depth + 1,
            max_depth,
            depth_factor * 0.5
        )


def update_recent_opp_list(opp_list: List, team_num):
    opp_list.pop()
    opp_list.insert(0, team_num)
    return opp_list


def nested_power_change(df, level_key: Tuple):
    team_state = TeamState()

    home_power_change = df.at[0, 'home_power_change']
    away_power_change = df.at[0, 'away_power_change']
    max_depth = 5

    home_team = df.at[0, 'home_team']
    away_team = df.at[0, 'away_team']
    
    home_team_recent_opp = \
        team_state.team_recent_opp(level_key, home_team)
    away_team_recent_opp = \
        team_state.team_recent_opp(level_key, away_team)

    team_info = \
        team_state.team_info(level_key)
    print(f"Home Recent: {home_team_recent_opp} Away Recent: {away_team_recent_opp}")
    # process_team_opponents(
    #     team_info,
    #     home_team_recent_opp,
    #     home_power_change,
    #     1,
    #     max_depth,
    #     depth_factor=(1.0 / 3.0)
    # )
    # process_team_opponents(
    #     team_info,
    #     away_team_recent_opp,
    #     away_power_change,
    #     1,
    #     max_depth,
    #     depth_factor=(1.0 / 3.0)
    # )
    team_state.update_team_info(
        level_key,
        home_team,
        away_team,
        df.at[0, 'home_team_power_ranking'],
        df.at[0, 'away_team_power_ranking']
    )
    # team_info[team_id.get(home_team.lower())].update(
    #     recent_opp=update_recent_opp_list(home_team_recent_opp, team_id.get(away_team.lower()))
    # )
    # team_info[team_id.get(away_team.lower())].update(
    #     recent_opp=update_recent_opp_list(away_team_recent_opp, team_id.get(home_team.lower()))
    # )


def run_calculations(df, level_key: Tuple):
    """
    Run all the calculations for the algorithm.
    :param df: DataFrame containing enriched data.
    :return: Final DataFrame with all calculations done.
    """
    # print(df)
    df = modify_game_scores(df)  # Modify the game scores
    # print(df.to_string())
    df = expected_wl(df)
    df = calculate_power_difference(df)
    nested_power_change(df, level_key)

    df = calculate_z_scores(df)  # Ensure Z-scores are calculated and included
    return df
