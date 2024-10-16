#
# teams.py
#
# Location for processing .csv file
# via Packard algorithm (utils).
#
# Returns JSON formatted info.
#

from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
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
        input_method: items.InputMethod = Depends(),
        csv_file: UploadFile = File()
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


# GET routes:
#
# Another get function just to retrieve all the sports for
# a specific sport, gender, and level
#
@router.get("/sports/teams", response_description="Display Teams Data")
async def list_teams(
    search_params: items.GeneralInputMethod = Depends()
):
    """
    Retrieve all teams based on sport type, gender, and level.
    
    - **search_params**: Filter the teams based on input parameters (sport_type, gender, level).
    """
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


@router.get("/sports/{sport_type}/teams", response_description="Display Teams Data")
async def list_teams_by_sport(
    sport_type: str,
    gender: str = None,
    level: str = None
):
    """
    Retrieve all teams for a specific sport, with optional filters.
    - **sport_type**: The type of sport (required).
    - **gender**: Filter by gender.
    - **level**: Filter by competition level.
    """
    query: Dict = {"sport_type": sport_type}

    # Optionally filter by gender and level
    if gender:
        query["gender"] = gender
    if level:
        query["level"] = level

    teams = await retrieve_sports(query, projection={"teams": 1, "_id": 0})

    if teams and 'teams' in teams:
        return {"message": "Teams data retrieved successfully", "data": teams['teams']}
    else:
        raise HTTPException(status_code=404, detail="No teams found for this sport")


@router.get("/sports/{sport_type}/teams/{team_name}", response_description="Display Sports Data")
async def list_sports(
    sport_type: str = None,
    team_name: str = None,
    input: items.GeneralInputMethod = Depends()
):
    """
    Fetch sports or team data based on query parameters.
    - If `sport_type` is provided, fetch teams for that sport.
    - If `team_name` is provided, fetch specific team details.
    - If no params, fetch all available sports.
    """
    query: Dict = {}

    # Build query based on sport_type and team_name
    if sport_type:
        query["sport_type"] = sport_type
    if team_name:
        query["team_name"] = team_name

    # Add additional query parameters if provided
    if input.gender:
        query["gender"] = input.gender
    if input.level:
        query["level"] = input.level

    # Fetch data from database
    sports_data = await retrieve_sports(query)

    # Return the appropriate response
    if sports_data:
        return sports_data
    else:
        raise HTTPException(status_code=404, detail="No sports data found")


# Update Sports (may involve some specifics but here is a start)
#
@router.put("/sports/teams/", response_description="Updating Team Info")
async def update_teams():
    pass


# Delete Sports (also will involve some more but basic start)
#
@router.delete("/sports/teams/", response_description="Deleting Team Info")
async def delete_teams():
    pass
