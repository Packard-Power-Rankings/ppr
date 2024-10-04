#
# teams.py
#
# Location for processing .csv file
# via Packard algorithm (utils).
#
# Returns JSON formatted info.
#

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from datetime import datetime
from typing import List, Any, Dict
from utils.json_helper import json_file_builder
from utils.update_algo_vals import update_values
from utils.algorithm.run import main
from service.teams import (
    add_sports_data,
    retrieve_sports
)
from schemas import items

router = APIRouter()


# CREATE routes:
@router.post("/", response_description="Added sports data into database")
async def add_sports(
        sport_type: str,
        gender: str,
        level: str,
        csv_file: Any,
        **algo_vals) -> Any:

    sport_doc: Dict = json_file_builder(sport_type, gender, level)

    if algo_vals:
        algo_update = update_values(
            (sport_type, gender, level),
            sport_doc,
            algo_vals
        )
        sport_doc['sports'][sport_type][gender][level].update(algo_update)

    team_info: List = sport_doc['sports'][sport_type][gender][level]['team']
    teams_data: List = await main(
        csv_file,
        (sport_type, gender, level)
    )
    for team_data in teams_data:
        team_info.append(team_data)

    sport_doc['sports'][sport_type][gender][level].update(team=team_info)
    sport_doc = jsonable_encoder(sport_doc)
    # Below I need the service connection for the database
    new_sports = await add_sports_data(sport_doc)
    return items.ResponseModel(new_sports, "Successfully added new sports")


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
