#
# teams.py
#
# Location for processing .csv file
# via Packard algorithm (utils).
#
# Returns JSON formatted info.
#

from fastapi import APIRouter, HTTPException
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


def get_level_mongoid(level_key: Tuple[str, str, str]) -> str:
    return LEVEL_CONSTANTS[level_key].get("_id")


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


# GET routes:
#
# Another get function just to retrieve all the sports for
# a specific sport, gender, and level
#
@router.get("/sports/teams", response_description="Display Teams Data")
async def list_teams(
    sport_type: str,
    gender: str,
    level: str
):
    """
    Retrieve all teams based on sport type, gender, and level.

    - **search_params**: Filter the teams based on input parameters
        (sport_type, gender, level).
    """
    # Need to add try blocks and exception handling below

    # level_key: Tuple = (sport_type, gender, level)
    # mongo_id = LEVEL_CONSTANTS[level_key].get("_id")
    mongo_id = get_level_mongoid(
        (sport_type, gender, level)
    )

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


@router.get(
    "/sports/{sport_type}/teams",
    response_description="Display Teams Data"
)
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
    # This function looks just like the one above
    # but the query for it is incorrect

    query: Dict = {"sport_type": sport_type}

    # Optionally filter by gender and level
    if gender:
        query["gender"] = gender
    if level:
        query["level"] = level

    teams = await retrieve_sports(query, projection={"teams": 1, "_id": 0})

    if teams and 'teams' in teams:
        return {
            "message":
                "Teams data retrieved successfully", "data": teams['teams']
            }
    else:
        raise HTTPException(
            status_code=404,
            detail="No teams found for this sport"
        )


# Changed function parameters as they are required for
# database query

@router.get(
    "/sports/{sport_type}/teams/{team_name}",
    response_description="Display Sports Data"
)
async def list_sports(
    sport_type: str,
    team_name: str,
    sport_input: items.GeneralInputMethod = Depends(...)
):
    """
    Fetch sports or team data based on query parameters.
    - If `sport_type` is provided, fetch teams for that sport.
    - If `team_name` is provided, fetch specific team details.
    - If no params, fetch all available sports.
    """
    query: Dict = query_params_builder()
    mongo_id: str = get_level_mongoid(
        (sport_type, sport_input.gender, sport_input.level)
    )
    query.update(
        _id=mongo_id,
        sport_type=sport_type,
        gender=sport_input.gender,
        level=sport_input.level
    )
    projection = {
        "teams": {"team_name": team_name},
        "_id": 0
    }

    # Fetch data from database
    sports_data = await retrieve_sports(query, projection)

    # Return the appropriate response
    if sports_data:
        return sports_data
    else:
        raise HTTPException(status_code=404, detail="No sports data found")


# Update Sports (may involve some specifics but here is a start)
#
@router.put("/sports/teams/", response_description="Updating Team Info")
async def update_teams(
    home_team: str,
    away_team: str,
    home_score: int | None,
    away_score: int | None,
    sport_type: str,
    gender: str,
    level: str
):
    if home_score is None and away_score is None:
        raise HTTPException(
            status_code=404,
            detail="Scores to update were both undefined"
        )

    query: Dict = query_params_builder()
    mongo_id = get_level_mongoid(
        (sport_type, gender, level)
    )
    query.update(
        _id=mongo_id,
        sport_type=sport_type,
        gender=gender,
        level=level
    )

    try:
        if home_score:
            home_list = await retrieve_sports(
                query,
                projection={
                    "teams": {"team_name": home_team},
                    "_id": 0
                }
            )
            if home_list:
                update_home: Dict = home_list["teams"][0]
                update_home.update(home_score=home_score)
            raise HTTPException(
                status_code=404,
                details=f"Home team: {home_team} was not found"
            )

            # Need the algorithm functions to update the
            # necessary values

        if away_score:
            away_list = await retrieve_sports(
                query,
                projection={
                    "teams": {"team_name": away_team},
                    "_id": 0
                }
            )
            if away_list:
                update_away: Dict = away_list[0]
                update_away.update(away_score=away_score)
            raise HTTPException(
                status_code=404,
                details=f"Away team: {away_team} was not found"
            )
            # Again need algorithm functions to update
            # the values
    except HTTPException as exc:
        raise HTTPException(
            status_code=500,
            details="Error has occurred"
        ) from exc


# Delete Sports (also will involve some more but basic start)
#
@router.delete("/sports/teams/", response_description="Deleting Team Info")
async def delete_teams():
    pass
