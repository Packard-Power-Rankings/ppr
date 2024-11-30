from __future__ import annotations
import traceback
from typing import Tuple, Dict, Annotated, Any
from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
    HTTPException,
    status,
    Body
)
from fastapi.security import OAuth2PasswordRequestForm
from schemas.items import (
    InputMethod,
    NewTeamList,
    UpdateTeamsData,
    Token,
    input_method_dependency,
    update_method
)
from service.admin_teams import AdminTeamsService
from service.admin_service import AdminServices

router = APIRouter()
admin_service = AdminServices()
_instance_cache: Dict[Tuple, "AdminTeamsService"] = {}


def admin_team_class(level_key: Tuple) -> "AdminTeamsService":
    if level_key not in _instance_cache:
        _instance_cache[level_key] = AdminTeamsService(level_key)
    return _instance_cache[level_key]


@router.post("/token/", response_model=Token, tags=["Admin"])
async def login_generate_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    admin_service: AdminServices = Depends()
):
    return await admin_service.login(form_data)


@router.post(
    "/upload_csv/",
    tags=["Admin"],
    dependencies=[Depends(AdminServices.get_current_admin)],
    description="Adds CSV File and Finds Missing Teams"
)
async def upload_csv(
    sports_input: InputMethod = Depends(input_method_dependency),
    csv_file: UploadFile = File()
):
    try:
        if not csv_file.filename.endswith(".csv"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be a csv"
            )
        level_key = (
            sports_input.sport_type,
            sports_input.gender,
            sports_input.level
        )
        team_services = admin_team_class(level_key)
        results = await team_services.store_csv_check_teams(
            sports_input.sport_type,
            sports_input.gender,
            sports_input.level,
            csv_file
        )
        return results
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Error"
        ) from exc


@router.post(
    "/add_teams/",
    tags=["Admin"],
    dependencies=[Depends(AdminServices.get_current_admin)],
    description="Adds Missing Teams To Database"
)
async def add_missing_teams(
    new_team: Annotated[NewTeamList, Body(embed=True)],
    sports_input: InputMethod = Depends(input_method_dependency)
):
    try:
        teams = new_team.model_dump()
        level_key = (
                sports_input.sport_type,
                sports_input.gender,
                sports_input.level
        )
        team_services = admin_team_class(level_key)
        results = await team_services.add_teams_to_db(teams['teams'])
        return results
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Error"
        ) from exc


@router.post(
    "/run_algorithm/",
    tags=["Admin"],
    dependencies=[Depends(AdminServices.get_current_admin)],
    description="Runs Main Algorithm"
)
async def main_algorithm_exc(
    iterations: int,
    sport_input: InputMethod = Depends(input_method_dependency)
):
    teams_service = admin_team_class(
        (
            sport_input.sport_type,
            sport_input.gender,
            sport_input.level
        )
    )
    results = await teams_service.run_main_algorithm(iterations)
    return results


@router.put(
    "/update_game/",
    tags=["Admin"],
    dependencies=[Depends(AdminServices.get_current_admin)],
    description="Updates Games and CSV File"
)
async def update_game(
    update_data: UpdateTeamsData = Depends(update_method),
    sport_input: InputMethod = Depends(input_method_dependency)
):
    team_service = admin_team_class(
        (
            sport_input.sport_type,
            sport_input.gender,
            sport_input.level
        )
    )
    results = await team_service.update_teams_info(
        update_data.home_team,
        update_data.home_score,
        update_data.away_team,
        update_data.away_score,
        update_data.date
    )
    return results


@router.delete(
    "/clear_season/",
    tags=["Admin"],
    dependencies=[Depends(AdminServices.get_current_admin)],
    description="Clears Season"
)
async def clear_season():
    pass
