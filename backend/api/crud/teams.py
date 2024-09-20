from typing import List, Any, Dict
from bson.objectid import ObjectId
from api.utils.dependencies import get_database
from api.utils.json_helper import json_file_builder
from api.utils.update_algo_vals import update_values
# from api.config import LEVEL_CONSTANTS

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
        # Function to update algorithm values if need be otherwise
        # they stay there constant value

        level_key = (sport_type, gender, level)
        sport_json_doc = update_values(
            level_key=level_key,
            sport_json_doc=sport_json_doc,
            algo_vals=algo_vals
        )
