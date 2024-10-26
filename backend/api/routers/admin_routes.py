from typing import List
from fastapi import APIRouter, Depends, File, UploadFile
from schemas.items import InputMethod, NewTeam, input_method_dependency

router = APIRouter()

@router.post("/upload_csv", tags=["Admin"])
async def upload_csv(
    sports_input: InputMethod = Depends(input_method_dependency),
    csv_file: UploadFile = File()
):
    pass


@router.post("/add_teams", tags=["Admin"])
async def add_missing_teams(
    new_teams: List[NewTeam]
):
    pass


@router.put("/update_game", tags=["Admin"])
async def update_game():
    pass


@router.delete("/clear_season", tags=["Admin"])
async def clear_season():
    pass
