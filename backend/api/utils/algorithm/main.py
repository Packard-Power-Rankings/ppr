import numpy as np  # For numerical operations
import pandas as pd
from typing import Tuple, Dict, Any, List
# from config.config import CONSTANTS_MAP


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


def power_change(actual_performance, expected_performance, k_value):
    return k_value * (actual_performance - expected_performance)


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


# def update_team_power_ranking(team, team_power_change, depth_factor):
#     team['power_ranking'][-1] = \
#         team['power_ranking'][-1] + team_power_change * depth_factor


def process_team_opponents(
    teams_id_dict: Dict,
    recent_opp_id: int,
    team_power_change: float,
    output_file
):
    # print(recent_opp_id)
    processing_stack = [(recent_opp_id, 1, 0)]

    while processing_stack:
        team_id, depth, exp = processing_stack.pop()
        output_file.write(f"Processing Stack: {processing_stack}\n")

        if depth > 5 or team_id == 0:
            continue

        current_team = teams_id_dict.get(team_id)
        
        output_file.write(f"Current Team: {current_team['team_name']}Current Team PR before change {current_team['power_ranking']}\n")

        depth_factor = (1.0 / 3.0) * (0.5 ** exp)
        current_change = depth_factor * team_power_change
        current_team['power_ranking'][-1] += current_change
        
        output_file.write(f"Current Team: {current_team['team_name']}Current Team PR after change {current_team['power_ranking']}\n")

        recent_opp = current_team.get('recent_opp')

        for _, opp_id in enumerate(recent_opp):
            if opp_id == 0:
                continue
            processing_stack.append((opp_id, depth + 1, exp + 1))


def update_recent_opp_list(opp_list: List, team_num):
    opp_list.pop()
    opp_list.insert(0, team_num)
    return opp_list


def nested_power_change(df, teams_id_dict, teams_names_dict, output_file):
    def calculate_power_change(row):
        home_team = teams_names_dict[row['home_team'].lower()]
        home_opponent_ids = home_team['recent_opp']
        home_team['power_ranking'][-1] += row['actual_home_performance']

        away_team = teams_names_dict[row['away_team'].lower()]
        away_team['power_ranking'][-1] += row['actual_away_performance']
        
        # print(f"Home Team PR before loop: {home_team['power_ranking']}")

        for _, opp_id in enumerate(home_opponent_ids):
            if opp_id == 0:
                continue
            process_team_opponents(
                teams_id_dict,
                opp_id,
                row['actual_home_performance'],
                output_file
            )
        # print(f"Home Team PR after loop: {home_team['power_ranking']}")
        # away_opponents_id = away_team['recent_opp']
        # for _, opp_id in enumerate(away_opponents_id):
        #     if opp_id == 0:
        #         continue
        #     process_team_opponents(
        #         teams_id_dict,
        #         opp_id,
        #         row['actual_away_performance'],
        #         output_file
        #     )
        # print(f"Home Team PR: {home_team['power_ranking']}")
        # print(f"Away Team PR: {away_team['power_ranking']}")
        teams_names_dict[row['home_team'].lower()]["recent_opp"] = \
            update_recent_opp_list(
                teams_names_dict[row["home_team"].lower()].get("recent_opp"),
                teams_names_dict[row["away_team"].lower()].get("team_id")
            )

        teams_names_dict[row["away_team"].lower()]["recent_opp"] = \
            update_recent_opp_list(
                teams_names_dict[row["away_team"].lower()].get("recent_opp"),
                teams_names_dict[row["home_team"].lower()].get("team_id")
            )

    df.apply(calculate_power_change, axis=1)


def run_calculations(df, teams_data, iterations: int):
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
    with open('output.txt', 'w', encoding='utf-8') as output_file:
        for _ in range(iterations):
            df = modify_game_scores(df)  # Modify the game scores
            df = expected_wl(df)
            df = calculate_power_difference(df)
            # nested_power_change(df, teams_id_dict, teams_names_dict, output_file)

    # print(teams_data)

    df = calculate_z_scores(df)  # Ensure Z-scores are calculated and included
    print(df.to_string())
    return df
