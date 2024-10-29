from __future__ import annotations
import traceback
from typing import List, Tuple
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from schemas.items import InputMethod, NewTeam, input_method_dependency
# from service.admin_service import AdminServices

router = APIRouter()

def admin_team_class(level_key: Tuple):
    from service.admin_teams import AdminTeamsService
    return AdminTeamsService(level_key)


@router.post("/upload_csv/", tags=["Admin"])
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
        )


@router.post("/add_teams", tags=["Admin"])
async def add_missing_teams(
    itter: int,
    sports_input: InputMethod = Depends(input_method_dependency)
):
    try:
        level_key = (
                sports_input.sport_type,
                sports_input.gender,
                sports_input.level
        )
        team_services = admin_team_class(level_key)
        results = await team_services.add_teams_to_db([], itter)
        return results
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Error"
        )


@router.put("/update_game", tags=["Admin"])
async def update_game():
    pass


@router.delete("/clear_season", tags=["Admin"])
async def clear_season():
    pass
