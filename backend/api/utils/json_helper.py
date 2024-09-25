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
        "sports": {
            sport_type: {
                gender: {
                    level: {
                        "k_value": 0.0,
                        "home_advantage": 0,
                        "average_game_score": 0,
                        "game_set_len": 0,
                        "team": [
                            {
                                #"id": 0,
                                "team_name": "",
                                "city": "",
                                "state": "",
                                "conference": "",
                                "division": "",
                                "wins": 0,
                                "losses": 0,
                                "z_score": 0.0,
                                "power_ranking": 0.0,
                                "season_opp": [
                                    {
                                        "opp_id": 0,
                                        "date": "1/15/2024"
                                    }
                                ],
                                "date": "12/01/2024"
                            }
                        ]
                    }
                }
            }
        }
    }
