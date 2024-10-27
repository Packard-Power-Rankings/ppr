from typing import Tuple, Dict, Any
from config.config import (
    STATES,
    LEVEL_CONSTANTS
)
from service.teams import (
    retrieve_sports,
    add_sports_data,
    update_sport
)


async def update_or_add_teams(
    home_team: Dict,
    away_team: Dict,
    level_key: Tuple
):
    """Updates or adds teams to database

    Args:
        home_team (Dict): Home Team Data
        away_team (Dict): Away Team Data
        level_key (Tuple): Level Key for Constants
    """

    query_base = {
        "_id": LEVEL_CONSTANTS[level_key].get("_id"),
        "sport_type": level_key[0],
        "gender": level_key[1],
        "level": level_key[2],
    }
    query_home = {
        **query_base,
        "teams.team_name": home_team['team_name']
    }
    query_away = {
        **query_base,
        "teams.team_name": away_team['team_name']
    }

    home_team_info = await retrieve_sports(query_home, None)
    away_team_info = await retrieve_sports(query_away, None)

    if home_team_info:
        update_home = {
            "$set": {
                "teams.$.power_ranking": home_team.get('power_ranking'),
                "teams.$.win_ratio": home_team.get('win_ratio'),
                "teams.$.prediction_info": home_team.get('prediction_info')
            },
            "$push": {
                "teams.$.season_opp": {
                    "$each": home_team.get("season_opp")
                }
            },
            "$inc": {
                "teams.$.wins": home_team.get('wins'),
                "teams.$.losses": home_team.get('losses')
            }
        }
        await update_sport(query_home, update_home)
    else:
        await add_sports_data(query_base, home_team)

    if away_team_info:
        update_away = {
            "$set": {
                "teams.$.power_ranking": away_team.get('power_ranking'),
                "teams.$.win_ratio": away_team.get('win_ratio'),
                "teams.$.prediction_info": away_team.get('prediction_info')
            },
            "$push": {
                "teams.$.season_opp": {
                    "$each": away_team.get("season_opp")}
            },
            "$inc": {
                "teams.$.wins": away_team.get('wins'),
                "teams.$.losses": away_team.get('losses'),
            }
        }
        await update_sport(query_away, update_away)
    else:
        await add_sports_data(query_base, away_team)


async def output_to_json(df, level_key: Tuple):
    """
    Converts the final DataFrame to JSON format and saves it to a file.
    Reformats the output so that each team has its own section.
    :param df: DataFrame containing the final processed data.
    :param output_file_path: The file path where the JSON will be saved.
    :return: None
    """
    # sport_type, gender, level = level_key
    # team_state = TeamState()
    # if level_key[2] == "college":
    #     team_name_map, team_id_map, team_division, team_conf = \
    #         CONSTANTS_MAP.get(level_key)
    # else:
    #     team_name_map, team_id_map, team_division = \
    #         CONSTANTS_MAP.get(level_key)
    #     team_conf = None

    # Need to calculate the wins and losses for
    # each team and store in the db

    # Loop through each row (game) in the DataFrame
    for _, row in df.iterrows():
        # Extract only the date part (no time) and convert to string
        game_date = row['date'].date().isoformat()

        # Power Ranking will change to a constant so we can update
        # easier and still store it into the database

        # Create a section for the home team
        home_win, home_loss = 0, 0
        away_win, away_loss = 0, 0

        if row['home_score'] > row['away_score']:
            home_win += 1
            away_loss += 1
        else:
            home_loss += 1
            away_win += 1

        home_team_data = {
            "team_id": team_state.team_id(level_key, row['home_team']),
            "team_name": row['home_team'],
            "city": '',
            "state": STATES[
                team_state.team_state_id(level_key, row['home_team'])
            ],
            "division": team_state.team_division(level_key, row['home_team']),
            "conference": team_state.team_conference(
                level_key, row['home_team']
            ),
            "power_ranking": row['home_team_power_ranking'],
            "win_ratio": row['home_team_win_ratio'],
            "wins": home_win,
            "losses": home_loss,
            "date": game_date,
            "season_opp": [
                {
                    "opponent_id": team_state.team_id(
                        level_key, row['away_team']),
                    "home_team": True,
                    "home_score": row['home_score'],
                    "away_score": row['away_score'],
                    "home_z_score": row['home_z_score'],
                    "away_z_score": row['away_z_score'],
                    "date": game_date
                }
            ]
            # "prediction_info": {
            #     "expected_performance": row['expected_performance_home'],
            #     "actual_performance": row['actual_performance_home'],
            #     "predicted_score": row['predicted_home_score']
            # }
        }

        # Create a section for the away team
        away_team_data = {
            "team_id": team_state.team_id(level_key, row['away_team']),
            "team_name": row['away_team'],
            "city": "",
            "state": STATES[
                team_state.team_state_id(level_key, row['away_team'])
            ],
            "division": team_state.team_division(level_key, row['away_team']),
            "conference": team_state.team_conference(
                level_key, row['away_team']
            ),
            "power_ranking": row['away_team_power_ranking'],
            "win_ratio": row['away_team_win_ratio'],
            "wins": away_win,
            "losses": away_loss,
            "date": game_date,
            "season_opp": [
                {
                    "opponent_id": team_state.team_id(
                        level_key, row['home_team']
                    ),
                    "home_team": False,
                    "home_score": row['home_score'],
                    "away_score": row['away_score'],
                    "home_z_score": row['home_z_score'],
                    "away_z_score": row['away_z_score'],
                    "date": game_date
                }
            ]
            # "prediction_info": {
            #     "expected_performance": row['expected_performance_away'],
            #     "actual_performance": row['actual_performance_away'],
            #     "predicted_score": row['predicted_away_score']
            # }
        }
        # Changed this to add or update home and away team data
        await update_or_add_teams(home_team_data, away_team_data, level_key)
