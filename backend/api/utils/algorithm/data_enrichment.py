import random
import pandas as pd


def enrich_data(df, k_value, home_advantage, average_game_score, teams):
    """
    Adds dummy values for R-value, home field advantage, power rankings,
    win/loss ratios, and AVEGAMESC.
    :param df: Cleaned DataFrame from data_cleaning.py.
    :return: DataFrame with dummy values added.
    """
    # team_state = TeamState()
    # # R-value (constant for all teams)
    # R_value = LEVEL_CONSTANTS[level_key].get("k_value")

    # # Home field advantage (constant for all home games)
    # home_advantage = LEVEL_CONSTANTS[level_key].get("home_advantage")

    # team_info, team_id = \
    #     CONSTANTS_MAP[level_key][0:2]

    # Generate power rankings and win/loss ratios for each team
    team_data = {}
    team_dict = {team_name["team_name"].lower(): team_name for team_name in teams}

    for team in pd.concat([df['home_team'], df['away_team']]).unique():
        if team.lower() in team_dict:
            team_data[team] = {
                "power_ranking": team_dict[team.lower()].get('power_ranking'),
                # Random win ratio between 30% and 90%
                "win_ratio": round(random.uniform(0.3, 0.9), 2)
            }
    # Add enrichment values to the DataFrame
    df['k_value'] = k_value
    df['AVEGAMESC'] = average_game_score

    # Adjust home field advantage: set to 0 for neutral sites (999)
    df['home_field_advantage'] = df['neutral_site'].apply(
        lambda x: home_advantage if x == 0 else 0)

    # Map power rankings and win/loss ratios to home and away teams
    df['home_team_power_ranking'] = df['home_team'].map(
        lambda x: team_data[x]['power_ranking'])
    df['away_team_power_ranking'] = df['away_team'].map(
        lambda x: team_data[x]['power_ranking'])
    df['home_team_win_ratio'] = df['home_team'].map(
        lambda x: team_data[x]['win_ratio'])
    df['away_team_win_ratio'] = df['away_team'].map(
        lambda x: team_data[x]['win_ratio'])

    return df
