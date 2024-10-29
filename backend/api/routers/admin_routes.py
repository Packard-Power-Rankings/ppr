from __future__ import annotations
import traceback
from typing import List, Tuple, Dict
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from schemas.items import InputMethod, NewTeam, input_method_dependency
from service.admin_teams import AdminTeamsService
# from service.admin_service import AdminServices

router = APIRouter()
_instance_cache: Dict[Tuple, "AdminTeamsService"] = {}


def admin_team_class(level_key: Tuple) -> "AdminTeamsService":
    if level_key not in _instance_cache:
        _instance_cache[level_key] = AdminTeamsService(level_key)
    return _instance_cache[level_key]


# def admin_team_class(level_key: Tuple):
#     from service.admin_teams import AdminTeamsService
#     return AdminTeamsService(level_key)


@router.post("/upload_csv", tags=["Admin"])
async def upload_csv(
    sports_input: InputMethod = Depends(input_method_dependency),
    csv_file: UploadFile = File()
):
    try:
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


@router.post("/add_teams", tags=["Admin"])
async def add_missing_teams(
    sports_input: InputMethod = Depends(input_method_dependency)
):
    try:
        level_key = (
                sports_input.sport_type,
                sports_input.gender,
                sports_input.level
        )
        team_services = admin_team_class(level_key)
        tmp_team = {
                "team_name": "Sul Ross",
                "division": None,
                "conference": None,
                "power_ranking": 286.53863361385584,
                "state": "Texas"
        }
        results = await team_services.add_teams_to_db(tmp_team)
        return results
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Error"
        ) from exc


@router.post("/run_algorithm", tags=["Admin"])
async def main_algorithm_exc(iterations: int):
    pass


@router.put("/update_game", tags=["Admin"])
async def update_game():
    pass


@router.delete("/clear_season", tags=["Admin"])
async def clear_season():
    pass
