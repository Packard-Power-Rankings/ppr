from typing import Tuple, Dict, Any
import json
from config.config import (
    CONSTANTS_MAP,
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
                "team.$.power_ranking": home_team.get('power_ranking'),
                "team.$.win_ratio": home_team.get('win_ratio'),
                "team.$.prediction_info": home_team.get('prediction_info')
            },
            "$push": {
                "team.$.season_opp": {
                    "$each": home_team.get("season_opp")
                }
            }
        }
        await update_sport(query_home, update_home)
    else:
        print("Hello home?")
        await add_sports_data(query_base, home_team)

    if away_team_info:
        update_away = {
            "$set": {
                "team.$.power_ranking": away_team.get('power_ranking'),
                "team.$.win_ratio": away_team.get('win_ratio'),
                "team.$.prediction_info": away_team.get('prediction_info')
            },
            "$push": {
                "team.$.season_opp": {
                    "$each": away_team.get("season_opp")}
            }
        }
        await update_sport(query_away, update_away)
    else:
        print("Hello away?")
        await add_sports_data(query_base, away_team)
        

def check_division_conf(
    team_name_map: Dict,
    team_id_map: Dict,
    team_division: Dict,
    team_conf: Dict | None,
    team_name: str
) -> Any:
    division = team_division[team_name_map[
                team_id_map.get(team_name)].get('division_id')]
    conf = team_conf[team_name_map[
            team_id_map.get(team_name)].get('conference_id')]
    
    return division, conf


async def output_to_json(df, level_key: Tuple):
    """
    Converts the final DataFrame to JSON format and saves it to a file.
    Reformats the output so that each team has its own section.
    :param df: DataFrame containing the final processed data.
    :param output_file_path: The file path where the JSON will be saved.
    :return: None
    """
    # sport_type, gender, level = level_key

    if level_key[2] == "college":
        team_name_map, team_id_map, team_division, team_conf = \
            CONSTANTS_MAP.get(level_key)
    else:
        team_name_map, team_id_map, team_division = \
            CONSTANTS_MAP.get(level_key)

    # Need to calculate the wins and losses for
    # each team and store in the db

    # Loop through each row (game) in the DataFrame
    for _, row in df.iterrows():
        # Extract only the date part (no time) and convert to string
        game_date = row['date'].date().isoformat()

        # Power Ranking will change to a constant so we can update
        # easier and still store it into the database

        # Create a section for the home team
        division_home, conf_home = check_division_conf(
            team_name_map,
            team_id_map,
            team_division,
            team_conf,
            row['home_team']
        )
        # print(row['home_team'])
        home_team_data = {
            "team_id": team_id_map.get(row['home_team']),
            "team_name": row['home_team'],
            "city": '',
            "state":
                    STATES[team_name_map[team_id_map.get(
                        row['home_team'])].get('state_id')].get('state_name'),
            "division": division_home,
            "conference": conf_home,
            "power_ranking": row['home_team_power_ranking'],
            "win_ratio": row['home_team_win_ratio'],
            "date": game_date,
            "season_opp": [
                {
                    "opponent_id": team_id_map.get(row['away_team']),
                    "home_team": True,
                    "home_score": row['home_score'],
                    "away_score": row['away_score'],
                    "power_difference": row['power_difference'],
                    "home_z_score": row['home_z_score'],
                    "away_z_score": row['away_z_score'],
                    "date": game_date
                }
            ],
            "prediction_info": {
                "expected_performance": row['expected_performance_home'],
                "actual_performance": row['actual_performance_home'],
                "predicted_score": row['predicted_home_score']
            }
        }

        division_away, conf_away = check_division_conf(
            team_name_map,
            team_id_map,
            team_division,
            team_conf,
            row['away_team']
        )
        # print(row['away_team'])
        # Create a section for the away team
        away_team_data = {
            "team_id": team_id_map.get(row['away_team']),
            "team_name": row['away_team'],
            "city": "",
            "state": STATES[team_name_map[team_id_map.get(
                    row['away_team'])].get("state_id")].get("state_name"),
            "division": division_away,
            "conference": conf_away,
            "power_ranking": row['away_team_power_ranking'],
            "win_ratio": row['away_team_win_ratio'],
            "date": game_date,
            "season_opp": [
                {
                    "opponent_id": team_id_map.get(row['home_team']),
                    "home_team": False,
                    "home_score": row['home_score'],
                    "away_score": row['away_score'],
                    "power_difference": row['power_difference'],
                    "home_z_score": row['home_z_score'],
                    "away_z_score": row['away_z_score'],
                    "date": game_date
                }
            ],
            "prediction_info": {
                "expected_performance": row['expected_performance_away'],
                "actual_performance": row['actual_performance_away'],
                "predicted_score": row['predicted_away_score']
            }
        }
        # Changed this to add or update home and away team data
        await update_or_add_teams(home_team_data, away_team_data, level_key)
