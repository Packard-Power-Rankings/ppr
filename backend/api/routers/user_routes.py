from fastapi import APIRouter, Depends
from schemas.items import GeneralInputMethod
from schemas import items
from typing import Dict, Tuple
from service.users_teams import UsersServices

router = APIRouter()
_instance_cache: Dict[Tuple, "UsersServices"] = {}


def users_class(level_key: Tuple) -> "UsersServices":
    if level_key not in _instance_cache:
        _instance_cache[level_key] = UsersServices(level_key)
    return _instance_cache[level_key]


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
    level_key: Tuple = (
            sport_type,
            search_params.gender,
            search_params.level
    )
    sports_data = users_class(level_key)
    results = sports_data.retrieve_sports_info()
    return results


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
    sports_data = users_class(level_key)
    results = sports_data.retrieve_team_info(team_name)
    return results


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
