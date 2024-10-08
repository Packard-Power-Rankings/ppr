#
# teams.py
#
# Location for processing .csv file
# via Packard algorithm (utils).
#
# Returns JSON formatted info.
#

from fastapi import APIRouter, File, UploadFile, Depends
# from fastapi.encoders import jsonable_encoder
# from datetime import datetime
from typing import Any, Dict, Tuple
from utils.json_helper import json_file_builder, query_params_builder
from utils.update_algo_vals import update_values
from utils.algorithm.run import main
from service.teams import (
    retrieve_sports
)
from config.config import LEVEL_CONSTANTS
from schemas import items

router = APIRouter()


# CREATE routes:
@router.post("/", response_description="Added sports data into database")
async def add_sports(
        input_method: items.InputMethod = Depends(...),
        csv_file: UploadFile = File(...)
) -> Any:
    # Going to be updating this function as I have changed
    # how the output function call does in the background

    algo_values = {
        "k_value": input_method.k_value,
        "home_advantage": input_method.home_advantage,
        "average_game_score": input_method.average_game_score,
        "game_set_len": input_method.game_set_len
    }

    level_key: Tuple = (
        input_method.sport_type,
        input_method.gender,
        input_method.level
    )

    if any(value for value in algo_values.values()):
        update_values(
            level_key,
            algo_values
        )

    await main(
        csv_file,
        level_key
    )
    # I will add back the ResponseModel here just not a priority at the
    # moment


# Another get function just to retrieve all the sports for
# a specific sport, gender, and level

@router.get("/sports/teams", response_description="Display Teams Data")
async def list_teams(
    search_params: items.GeneralInputMethod = Depends(...)
):
    level_key: Tuple = (
        search_params.sport_type,
        search_params.gender,
        search_params.level
    )
    mongo_id = LEVEL_CONSTANTS[level_key].get("_id")

    query: Dict = query_params_builder()
    query.update(
        _id=mongo_id,
        sport_type=search_params.sport_type,
        gender=search_params.gender,
        level=search_params.level
    )

    projection = {"teams": 1, "_id": 0}

    teams = await retrieve_sports(query, projection)
    if teams and 'teams' in teams:
        return teams['teams']
    return "No teams found"

# READ routes:
@router.get("/sports/teams/{id}", response_description="Display sports data")
async def list_sports(
    sport_id: int,
    sport_type: str,
    gender: str,
    level: str,
):
    try:
        # Create the query based on the provided parameters
        query: Dict = {"id": sport_id}  # Initialize with ID as it's mandatory

        # Generate sport_doc just like in the POST route
        sport_doc: Dict = json_file_builder(sport_type, gender, level)

        # Fetch sports data using the query
        sports = await retrieve_sports(query, sport_id)

        # Check if sports data is found
        if sports:
            team_info = \
                sport_doc['sports'][sport_type][gender][level].get('team', [])

            response_data = {
                "sport": sport_doc,
                "teams": team_info,
                "sports_data": sports
            }
            return items.ResponseModel(
                response_data,
                "Sports data retrieved successfully"
            )
        return items.ResponseModel([], "No sports data found")

    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}


# Update Sports (may involve some specifics but here is a start)

@router.put("/sports/teams/", response_description="Updating Team Info")
async def update_teams():
    pass


# Delete Sports (also will involve some more but basic start)

@router.delete("/sports/teams/", response_description="Deleting Team Info")
async def delete_teams():
    pass
