from typing import List, Any, Dict
from bson.objectid import ObjectId
from api.utils.dependencies import get_database
from api.utils.json_helper import json_file_builder
from api.config import LEVEL_CONSTANTS

db = get_database()
teams_collection = db.get_collection("sports")


async def create_sport(
        sport_type: str,
        gender: str,
        level: str,
        team_data: List,
        **algo_vals
):
    sport_json_doc = json_file_builder(
        sport_type=sport_type,
        gender=gender,
        level=level
    )

    if algo_vals:
        sport_json_doc['sports'][sport_type][gender][level]['k_value'] = \
            algo_vals.get(
                "k_value",
                LEVEL_CONSTANTS[
                    (sport_type, gender, level): ['k_value']
                ]
            )
        sport_json_doc['sports'][sport_type][gender][level]['home_advantage'] \
            = algo_vals.get(
                "home_advantage",
                LEVEL_CONSTANTS[
                    (sport_type, gender, level): ['home_advantage']
                ]
            )
        sport_json_doc['sports'][sport_type][gender][level]['average_game_score'] \
            = algo_vals.get(
                "average_game_score",
                LEVEL_CONSTANTS[
                    (sport_type, gender, level): ['average_game_score']
                ]
            )
        sport_json_doc['sports'][sport_type][gender][level]['game_set_len'] \
            = algo_vals.get(
                "game_set_len",
                LEVEL_CONSTANTS[
                    (sport_type, gender, level): ['game_set_len']
                ]
            )
