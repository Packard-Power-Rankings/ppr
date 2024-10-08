"""
    :Helper function for building out json file to
    :store in mongodb
"""

from typing import Dict


def json_file_builder(sport_type: str, gender: str, level: str) -> Dict:
    """Function that defines the structure for
    json file for mongodb

    Args:
        sport_type (str): Type Of Sport
        gender (str): Men's/Women's
        level (str): College/High School

    Returns:
        dict: A dictionary structured for json conversion
    """

    return {
        "_id": "",
        "sports_type": sport_type,
        "gender": gender,
        "level": level,
        "team": [
            {
                "team_id": 1,
                'team_name': '',
                'city': '',
                'state': '',
                'power_ranking': 0.0,
                'win_ratio': 0.0,
                'date': '1/15/2024',
                "season_opp": [
                    {
                        'id': 2,
                        'home_game_bool': False,
                        'home_score': 0,
                        'away_score': 0,
                        'power_difference': 0.0,
                        'home_zscore': 0.0,
                        'away_zscore': 0.0,
                        'date': '1/15/2024'
                    }
                ],
                "prediction_info": {
                    'expected_performance': 0.0,
                    'actual_performance': 0,
                    'predicted_score': 0.0
                }
            }
        ]
    }
