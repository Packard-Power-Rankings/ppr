from typing import Dict, Tuple, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, status, Depends, Header
from api.schemas.items import InputMethod
# from api.schemas import items
from api.service.users_teams import UsersServices
from api.service.admin_service import AdminServices
import os

router = APIRouter()
_instance_cache: Dict[Tuple, "UsersServices"] = {}


def users_class(level_key: Tuple) -> "UsersServices":
    if level_key not in _instance_cache:
        _instance_cache[level_key] = UsersServices(level_key)
    return _instance_cache[level_key]


@router.get("/teams", response_description="Display Teams Data")
async def list_teams(
    items: InputMethod = Depends()
):
    """
    Retrieve all teams for a specific sport, with optional filters.
    - **sport_type**: The type of sport (required).
    - **gender**: Filter by gender.
    - **level**: Filter by competition level.
    """
    level_key: Tuple = (
        items.sport_type,
        items.gender,
        items.level
    )
    sports_data = users_class(level_key)
    results = await sports_data.retrieve_sports_info()  # Await the async method
    return results


@router.get("/teams/{team_name}", response_description="Display Team Specific Data")
async def list_team_info(
    team_name: str,
    items: InputMethod = Depends()
):
    """
    Fetch sports or team data based on query parameters.
    """
    level_key: Tuple = (
        items.sport_type,
        items.gender,
        items.level
    )
    sports_data = users_class(level_key)
    results = await sports_data.retrieve_team_info(team_name)
    
    if results is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return results


@router.get("/predictions", response_description="Get Sports Teams")
async def get_sports_team_names(
    items: InputMethod = Depends()
):
    level_key: Tuple = (
        items.sport_type,
        items.gender,
        items.level
    )
    sports_data = users_class(level_key)
    return await sports_data.retrieve_team_names()



@router.get("/predictions/{team_one}/{team_two}/{home_field_adv}", response_description="Get Predictions")
async def get_game_predictions(
    team_one: str,
    team_two: str,
    home_field_adv: bool,
    items: InputMethod = Depends()
):
    level_key: Tuple = (
        items.sport_type,
        items.gender,
        items.level
    )
    sports_data = users_class(level_key)
    score_predictions = \
        await sports_data.score_predictions(team_one, team_two, home_field_adv)
    return score_predictions








# ---- NEW: request model for admin creation ----
class AdminCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)

# ---- NEW: simple setup guard with X-Setup-Token ----
SETUP_TOKEN = os.getenv("SETUP_TOKEN")

async def require_setup_token(x_setup_token: Optional[str] = Header(None)):
    # only allow if the header matches the env var
    if SETUP_TOKEN:
        if x_setup_token is None or x_setup_token != SETUP_TOKEN:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid X-Setup-Token",
            )

@router.post(
    "/admin/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_setup_token)],
)
async def create_admin(body: AdminCreate):
    """
    Create the first admin account using AdminServices.create_admin().
    This will hash the password correctly.
    """
    svc = AdminServices()

    # optional safety: block creating a second admin unless you want multiple
    count = await svc.admin_collection.count_documents({})
    if count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Admin already exists",
        )

    admin_id = await svc.create_admin(body.username, body.password)
    return {"ok": True, "id": str(admin_id), "username": body.username}
