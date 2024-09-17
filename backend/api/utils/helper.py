def build_json_file(sport_type: str, gender: str, level: str):
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
