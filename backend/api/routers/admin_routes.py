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
from schemas.items import InputMethod, NewTeamList, input_method_dependency
from service.admin_teams import AdminTeamsService
from service.admin_service import AdminServices
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from schemas.items import TokenData

router = APIRouter()
admin_service = AdminServices()
_instance_cache: Dict[Tuple, "AdminTeamsService"] = {}


def admin_team_class(level_key: Tuple) -> "AdminTeamsService":
    if level_key not in _instance_cache:
        _instance_cache[level_key] = AdminTeamsService(level_key)
    return _instance_cache[level_key]


@router.post("/add-admin/", tags=["Admin"])
async def add_admin(
    username: str, 
    password: str
) -> Any:
    """
    ___
    DO NOT USE THIS METHOD IN PRODUCTION!
    ___
    A NEW ADMINISTRATOR WILL BE CREATED!
    ___
    
    Adds a new admin to the database.
    
    Args:
        username (str): The username of the new admin.
        password (str): The password of the new admin.

    Returns:
        JSONResponse: Confirmation of the new admin creation along with an access token.
    """
    try:
        # Create the new admin account
        admin_id = await admin_service.create_admin(username, password)
        
        # Generate an access token for the newly created admin
        token = admin_service.generate_access_token({"sub": username})

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "Admin created successfully",
                "admin_id": admin_id,
                "access_token": token,
                "token_type": "bearer"
            }
        )
    except HTTPException as exc:
        raise exc  # Reraise HTTP errors to propagate them
    except Exception as exc:
        print(f"Unexpected error: {exc}")  # Log the exception for debugging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {exc}"
        )


@router.post("/login/", tags=["Admin"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Handles admin login by verifying credentials and generating an access token.
    
    Args:
        form_data (OAuth2PasswordRequestForm): Form data with username and password.

    Returns:
        JSONResponse: Contains access token and token type if successful.
    """
    try:
        # Use AdminServices to verify the username and password
        token = await admin_service.verify_admin(form_data.username, form_data.password)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "access_token": token,
                "token_type": "bearer"
            }
        )
    except HTTPException as exc:
        raise exc  # Reraise to propagate specific HTTP errors
    except Exception as exc:
        print(f"Unexpected error: {exc}")  # Log the exception for debugging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {exc}"  # Show detailed error for testing
        )


@router.post("/upload_csv/", tags=["Admin"])
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


@router.post("/add_teams/", tags=["Admin"])
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


@router.post("/run-algorithm", tags=["Admin"])
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


@router.put("/update_game", tags=["Admin"])
async def update_game():
    pass


@router.delete("/clear_season", tags=["Admin"])
async def clear_season():
    pass
