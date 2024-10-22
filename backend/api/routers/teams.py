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
    retrieve_sports,
    delete_sport,
    update_sport,
    add_sports_data
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
# @router.get("/sports/teams", response_description="Display Teams Data")
# async def list_teams(
#     search_params: items.GeneralInputMethod = Depends()
# ):
#     """
#     Retrieve all teams based on sport type, gender, and level.
    
#     - **search_params**: Filter the teams based on input parameters (sport_type, gender, level).
#     """
#     level_key: Tuple = (
#         search_params.sport_type,
#         search_params.gender,
#         search_params.level
#     )
#     mongo_id = LEVEL_CONSTANTS[level_key].get("_id")

#     query: Dict = query_params_builder()
#     query.update(
#         _id=mongo_id,
#         sport_type=search_params.sport_type,
#         gender=search_params.gender,
#         level=search_params.level
#     )

#     projection = {"teams": 1, "_id": 0}

#     teams = await retrieve_sports(query, projection)
#     if teams and 'teams' in teams:
#         return teams['teams']
#     return "No teams found"


@router.get("/{sport_type}/", response_description="Display Teams Data")
async def list_teams(
    sport_type: str,
    search_params: items.GeneralInputMethod = Depends()
):
    """
    Retrieve all teams for a specific sport, with optional filters.
    - **sport_type**: The type of sport (required).
    - **gender**: Filter by gender.
    - **level**: Filter by competition level.
    """
    try:
        level_key: Tuple = (
            sport_type,
            search_params.gender,
            search_params.level
        )

        query: Dict = query_params_builder()
        mongo_id = LEVEL_CONSTANTS[level_key].get("_id")
        query.update(
            _id=mongo_id,
            sport_type=sport_type,
            gender=search_params.gender,
            level=search_params.level
        )

        projection = {"teams": 1, "_id": 0}

        # Fetch data from database
        teams = await retrieve_sports(query, projection)

        if teams and 'teams' in teams:
            return {"message": "Teams data retrieved successfully", "data": teams['teams']}
        else:
            raise HTTPException(status_code=404, detail="No teams found for this sport")

    except Exception as e:
        # Log the error and raise 500 Internal Server Error
        print(f"Error in fetching teams for sport_type={sport_type}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.get("/{sport_type}/{team_name}/", response_description="Display Team Specific Data")
async def list_teams_info(
    sport_type: str,
    team_name: str,
    search_params: items.GeneralInputMethod = Depends()
):
    """
    Fetch sports or team data based on query parameters.
    - If `sport_type` is provided, fetch teams for that sport.
    - If `team_name` is provided, fetch specific team details.
    - If no params, fetch all available sports.
    """
    level_key: Tuple = (
        sport_type,
        search_params.gender,
        search_params.level,
    )

    query: Dict = query_params_builder()
    mongo_id = LEVEL_CONSTANTS[level_key].get("_id")
    query.update(
        _id=mongo_id,
        sport_type=sport_type,
        gender=search_params.gender,
        level=search_params.level,
        teams={
            "$elemMatch": {
                "team_name": {
                    "$regex": f"^{team_name}$",
                    "$options": "i"  # Case-insensitive search
                }
            }
        }
    )

    projection = {"teams": 1, "_id": 0}

    # Fetch data from database
    team_data = await retrieve_sports(query, projection)

    if team_data:
        return team_data
    else:
        raise HTTPException(status_code=404, detail="No sports data found")


# Update Sports (may involve some specifics but here is a start)
#
@router.put("/admin/{sport_type}/{team_name}", response_description="Updating Team Info")
async def update_teams(
    sport_type: str,
    team_name:str,
    search_params: items.GeneralInputMethod = Depends()
):
    """
    Updates a specific team's information based on the provided input.

    Args:
        sport_type (str): The type of sport (e.g., basketball, football).
        team_name (str): The name of the sport.
        search_params (GeneralInputMethod): Additional input values for update, passed via dependency.

    Returns:
        JSON response indicating success or failure.
    """
    try:
        updated_team = await update_sport(
            {"sport_type": sport_type,
             "team_name": team_name
            }
        )
        if updated_team:
            return {"message": f"Team '{search_params.team_name}' updated successfully"}
        raise HTTPException(status_code=404, detail="Team not found or no changes made")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# Delete Sports (also will involve some more but basic start)
#
@router.delete("/admin/{sport_type}/{team_name}", response_description="Deleting Team Info")
async def delete_teams(
    sport_type: str,
    team_name: str
):
    """
    Deletes specific team data such as scores, win/loss ratios, and performance information.

    Args:
        sport_type (str): The type of sport (e.g., basketball, football).
        team_name (str): The name of the team to delete data from.

    Returns:
        JSON response indicating success or failure.
    """
    try:
        response = await delete_sport(
            {"sport_type": sport_type},
            sport_type,
            team_name
        )
        if response:
            return {"message": f"Team '{team_name}' deleted successfully"}
        raise HTTPException(status_code=404, detail="Team not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
