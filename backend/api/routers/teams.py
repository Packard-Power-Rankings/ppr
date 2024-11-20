#
# teams.py
#
# Location for processing .csv file
# via Packard algorithm (utils).
#
# Returns JSON formatted info.
# This will get reduced to very a smaller
# structure versus what it is now
#

import csv
from io import StringIO
from fastapi import APIRouter, HTTPException, Depends, UploadFile
import traceback
# from fastapi.encoders import jsonable_encoder
# from datetime import datetime
from typing import Any, Dict, Tuple, List
from utils.json_helper import json_file_builder, query_params_builder
from utils.update_algo_vals import update_values
from utils.algorithm.run import main
from service.teams import (
    retrieve_sports,
    clear_season,
    add_csv_file,
    # delete_sport,
    # update_sport,
    # add_sports_data,
    # find_teams
)
from config.constants import LEVEL_CONSTANTS
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
        csv_file: UploadFile,
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

    query_csv = {
        "sport_type": sport_type,
        "gender": gender,
        "level": level
    }
    try:
        await add_csv_file(
            query_csv,
            csv_file
        )
        csv_file.file.close()
        await main(level_key)
        return {"success": "Successful upload"}
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(
            status_code=404, detail="Error has occurred"
        ) from exc
    # I will add back the ResponseModel here just not a priority at the
    # moment


@router.post(
    "/upload_csv",
    description="Upload and checks for missing teams in db"
)
async def upload_csv_check_teams(
    sport_type: str,
    gender: str,
    level: str,
    csv_file: UploadFile,
):
    pass

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


# @router.get("/{sport_type}/", response_description="Display Teams Data")
# async def list_teams(
#     sport_type: str,
#     search_params: items.GeneralInputMethod = Depends()
# ):
#     """
#     Retrieve all teams for a specific sport, with optional filters.
#     - **sport_type**: The type of sport (required).
#     - **gender**: Filter by gender.
#     - **level**: Filter by competition level.
#     """
#     try:
#         level_key: Tuple = (
#             sport_type,
#             search_params.gender,
#             search_params.level
#         )

#         query: Dict = query_params_builder()
#         mongo_id = LEVEL_CONSTANTS[level_key].get("_id")
#         query.update(
#             _id=mongo_id,
#             sport_type=sport_type,
#             gender=search_params.gender,
#             level=search_params.level
#         )

#         projection = {"teams": 1, "_id": 0}

#         # Fetch data from database
#         teams = await retrieve_sports(query, projection)

#         if teams and 'teams' in teams:
#             return {"message": "Teams data retrieved successfully", "data": teams['teams']}
#         else:
#             raise HTTPException(status_code=404, detail="No teams found for this sport")

#     except Exception as e:
#         # Log the error and raise 500 Internal Server Error
#         print(f"Error in fetching teams for sport_type={sport_type}: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# @router.get("/{sport_type}/{team_name}/", response_description="Display Team Specific Data")
# async def list_team_info(
#     sport_type: str,
#     team_name: str,
#     search_params: items.GeneralInputMethod = Depends()
# ):
#     """
#     Fetch sports or team data based on query parameters.
#     - If `sport_type` is provided, fetch teams for that sport.
#     - If `team_name` is provided, fetch specific team details.
#     - If no params, fetch all available sports.
#     """
#     level_key: Tuple = (
#         sport_type,
#         search_params.gender,
#         search_params.level
#     )

#     query: Dict = query_params_builder()
#     mongo_id = LEVEL_CONSTANTS[level_key].get("_id")
#     query.update(
#         _id=mongo_id,
#         sport_type=sport_type,
#         gender=search_params.gender,
#         level=search_params.level,
#         teams={
#             "$elemMatch": {
#                 "team_name": {"$regex": f"^{team_name}$", "$options": "i"}
#             }
#         }
#     )

#     projection = {
#         "teams.$": 1,
#         "_id": 0
#     }

#     # Fetch data from database
#     team_data = await retrieve_sports(query, projection)

#     if team_data:
#         return team_data
#     else:
#         raise HTTPException(status_code=404, detail="No sports data found")


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
async def delete_teams(
    sport_type: str,
    gender: str,
    level: str
):
    try:
        query: Dict = query_params_builder()
        query.update(
            _id=get_level_mongoid((sport_type, gender, level)),
            sport_type=sport_type,
            gender=gender,
            level=level
        )
        update_params = {
            "$unset": {
                "teams.$[team].win_ratio": 0.0,
                "teams.$[team].wins": 0,
                "teams.$[team].losses": 0,
            },
            "$set": {
                "teams.$[team].season_opp": []
            }
        }
        array_filters = [{"team": {"$exists": True}}]

        result = clear_season(query, update_params, array_filters)

        if result.matched_count == 0:
            raise HTTPException(
                status_code=404,
                details="No matching document based on query"
            )
        if result.modified_count == 0:
            raise HTTPException(
                status_code=404,
                details="No fields were modified"
            )
        return items.ResponseModel(
                result,
                "Fields Cleared For All Teams"
            )
    except HTTPException as exc:
        raise HTTPException(status_code=500, details="Error Occurred") from exc
