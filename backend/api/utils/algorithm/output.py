from typing import Tuple, Dict
import json
from ...config import (
    CONSTANTS_MAP,
    STATES
)
from ...service.teams import retrieve_sports


def output_to_json(df, level_key: Tuple):
    """
    Converts the final DataFrame to JSON format and saves it to a file.
    Reformats the output so that each team has its own section.
    :param df: DataFrame containing the final processed data.
    :param output_file_path: The file path where the JSON will be saved.
    :return: None
    """
    sport_type, gender, level = level_key
    
    if level == "college":
        team_name_map, team_id_map, team_division, team_conf = \
            CONSTANTS_MAP.get(level_key)
    else:
        team_name_map, team_id_map, team_division = \
            CONSTANTS_MAP.get(level_key)

    # List to hold the formatted data
    output_data = []

    # Loop through each row (game) in the DataFrame
    for _, row in df.iterrows():
        # Extract only the date part (no time) and convert to string
        game_date = row['date'].date().isoformat()
        
        """
            Changing output to:
            home_team_data = {
                'team_id': id_num,
                'team_name': 'team_name',
                'city': '',
                'state': 'state',
                'power_rank': 0.0,
                'win_ratio': 0.0
                "data": date,
                'season_opp': [
                    {
                        'id': id_num,
                        'home_team': bool,
                        'home_score': 0,
                        'away_score': 0,
                        'power_diff': 0.0,
                        'home_zscore': 0.0,
                        'away_zscore': 0.0,
                        'data': date
                    }
                ],
                "prediction_info": {
                    'expected_performance': 0.0,
                    'actual_performance': bool,
                    'predicted_score': 0.0
                }
            }
        """

        # Power Ranking will change to a constant so we can update
        # easier and still store it into the database

        # Create a section for the home team
        home_team_data = {
            "team_id": team_id_map.get(row['home_team']),
            "team_name": row['home_team'],
            "city": '',
            "state":
                    STATES[team_name_map[team_id_map.get(
                        row['home_team'])].get('state_id')].get('state_name'),
            "division":
                    team_division[
                        team_name_map[
                            team_id_map.get(row['home_team'])
                        ].get('division_id')],
            "conference":
                    team_conf[
                        team_name_map[
                            team_id_map.get(row['home_team'])
                        ].get('conference_id')
                    ] if team_conf else None,
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
        query_home_team = {
            "sport_type": sport_type,
            "gender": gender,
            "level": level,
            "team_name": home_team_data.get('home_team')
        }
        home_team = retrieve_sports(query_home_team, 0)
        # output_data.append(home_team_data)

        # Create a section for the away team
        away_team_data = {
            "team_id": team_id_map.get(row['away_team']),
            "team_name": row['away_team'],
            "city": "",
            "state": STATES[team_name_map[team_id_map.get(
                    row['away_team'])].get("state_id")].get("state_name"),
            "division":
                team_division[
                    team_name_map[
                        team_id_map.get(row['away_team'])
                    ].get('division_id')
                ],
            "conference":
                team_conf[
                        team_name_map[
                            team_id_map.get(row['away_team'])
                        ].get('conference_id')
                    ] if team_conf else None,
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
        output_data.append(away_team_data)

    # Write the JSON data to a file
    # with open(output_file_path, 'w') as json_file:
    #     json.dump(output_data, json_file, indent=4)

    # print(f"Results saved to {output_file_path}")
    return output_data
