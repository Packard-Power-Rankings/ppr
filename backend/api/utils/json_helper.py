"""
    :Helper function for building out json file to
    :store in mongodb
"""


def json_file_builder(sport_type: str, gender: str, level: str) -> dict:
    # Here you can define actual values for k_value, home_advantage, etc.
    return {
        "sports": {
            sport_type: {
                gender: {
                    level: {
                        "k_value": 0.0,  # Replace with actual logic to compute this value
                        "home_advantage": 0,  # Replace with actual logic
                        "average_game_score": 0,  # Replace with actual logic
                        "game_set_len": 0,  # Replace with actual logic
                        "team": [
                            {
                                "id": 1,  # Replace with actual ID or logic
                                "city": "Sample City",  # Replace with actual data
                                "state": "Sample State",  # Replace with actual data
                                "conference": "Sample Conference",  # Replace with actual data
                                "division": "Sample Division",  # Replace with actual data
                                "score": 0,  # Replace with actual logic
                                "z-score": 0.0,  # Replace with actual logic
                                "power_ranking": 0.0,  # Replace with actual logic
                                "season_opp": [
                                    {
                                        "opp_id": 2,  # Replace with actual opponent ID
                                        "date": "2024-01-01"  # Replace with actual date
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
        }
    }
