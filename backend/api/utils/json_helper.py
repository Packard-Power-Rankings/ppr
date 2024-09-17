"""
    :Helper function for building out json file to
    :store in mongodb
"""


def json_file_builder(sport_type: str, gender: str, level: str):
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
                        "k_value": float,
                        "home_advantage": int,
                        "average_game_score": int,
                        "game_set_len": int,
                        "team": [
                            {
                                "id": int,
                                "city": str,
                                "state": str,
                                "conference": str,
                                "division": str,
                                "score": int,
                                "z-score": float,
                                "power_ranking": float,
                                "season_opp": [
                                    {
                                        "opp_id": int,
                                        "date": str
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
        }
    }
