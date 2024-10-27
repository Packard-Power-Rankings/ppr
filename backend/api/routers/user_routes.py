from fastapi import APIRouter
from schemas.items import GeneralInputMethod

router = APIRouter()


@router.get("/teams_data", tags=["User"])
async def get_teams_data(sport_input: GeneralInputMethod):
    pass


@router.get("/team_data/{team_name}", tags=["User"])
async def get_team_data(
    team_name: str,
    sport_input: GeneralInputMethod
):
    pass


@router.get("/predictions/{team_one}/{team_two}/{home_field_adv}", tags=["User"])
async def get_game_predicitions(
    team_one: str,
    team_two: str,
    home_field_adv: float,
    sport_input: GeneralInputMethod
):
    pass
