#
# teams.py
#
# Location for processing .csv file
# via Packard algorithm (utils).
#
# Returns JSON formatted info.
#

from fastapi import APIRouter
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
        sport_type: str,
        gender: str,
        level: str,
        csv_file: Any,
        algo_values: Dict
) -> Any:

    level_key: Tuple = (sport_type, gender, level)

    if any(value for value in algo_values.values()):
        update_values(
            level_key,
            algo_values
        )
    # Need to store the csv file in db instead of sending it to main
    # algorithm function

    

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
    sport_type: str,
    gender: str,
    level: str
):
    # Need to add try blocks and exception handling below

    level_key: Tuple = (sport_type, gender, level)
    mongo_id = LEVEL_CONSTANTS[level_key].get("_id")

    query: Dict = query_params_builder()
    query.update(
        _id=mongo_id,
        sport_type=sport_type,
        gender=gender,
        level=level
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
