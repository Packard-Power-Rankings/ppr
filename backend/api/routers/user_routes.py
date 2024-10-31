from fastapi import APIRouter, HTTPException, Depends
from schemas.items import GeneralInputMethod
from schemas import items
from utils.json_helper import query_params_builder
from typing import Dict, Tuple
from config.config import LEVEL_CONSTANTS
from service.teams import (
    retrieve_sports
)

router = APIRouter()


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
async def list_team_info(
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
        search_params.level
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
                "team_name": {"$regex": f"^{team_name}$", "$options": "i"}
            }
        }
    )

    projection = {
        "teams.$": 1,
        "_id": 0
    }

    # Fetch data from database
    team_data = await retrieve_sports(query, projection)

    if team_data:
        return team_data
    else:
        raise HTTPException(status_code=404, detail="No sports data found")


# @router.get("/teams_data", tags=["User"])
# async def get_teams_data(sport_input: GeneralInputMethod):
#     pass


# @router.get("/team_data/{team_name}", tags=["User"])
# async def get_team_data(
#     team_name: str,
#     sport_input: GeneralInputMethod
# ):
#     pass


@router.get("/predictions/{team_one}/{team_two}/{home_field_adv}", tags=["User"])
async def get_game_predicitions(
    team_one: str,
    team_two: str,
    home_field_adv: float,
    sport_input: GeneralInputMethod
):
    pass
