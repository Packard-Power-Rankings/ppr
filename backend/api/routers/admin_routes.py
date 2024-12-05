"""Routes for Admin CRUD operations

    Raises:
        HTTPException: 500_INTERNAL_SERVER_ERROR
        HTTPException: 500_INTERNAL_SERVER_ERROR
        HTTPException: 500_INTERNAL_SERVER_ERROR
        HTTPException: 500_INTERNAL_SERVER_ERROR
        HTTPException: 500_INTERNAL_SERVER_ERROR
        HTTPException: 500_INTERNAL_SERVER_ERROR
"""


from __future__ import annotations
import traceback
from typing import Tuple, Dict, Annotated, Any
from celery.result import AsyncResult
from celery import states
from service.tasks import run_main_algorithm
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
from fastapi.responses import JSONResponse
from api.service.tasks import run_main_algorithm
from api.schemas.items import (
    InputMethod,
    NewTeamList,
    UpdateTeamsData,
    Token,
    input_method_dependency,
    update_method
)
from api.service.admin_teams import AdminTeamsService
from api.service.admin_service import AdminServices
from api.service.celery import celery

router = APIRouter()
admin_service = AdminServices()
_instance_cache: Dict[Tuple, "AdminTeamsService"] = {}


def admin_team_class(level_key: Tuple) -> "AdminTeamsService":
    """Admin singleton for queueing instances of Admin
    Teams Service.

    Args:
        level_key (Tuple): Tuple with level key

    Returns:
        AdminTeamsService: The cached object
    """
    if level_key not in _instance_cache:
        _instance_cache[level_key] = AdminTeamsService(level_key)
    return _instance_cache[level_key]


@router.post("/token/", response_model=Token, tags=["Admin"])
async def login_generate_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    admin_service: AdminServices = Depends()
):
    """Generates the login token based on the verification

    Args:
        form_data (OAuth2PasswordRequestForm, optional): Password and Username.
        Defaults to Depends().
        admin_service (AdminServices, optional): Admin Services Object.
        Defaults to Depends().

    Returns:
        TokenData: Login token
    """
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
    """Endpoint for uploading a csv file and checking if teams are missing

    Args:
        sports_input (InputMethod, optional): Input for specific sports info.
        Defaults to Depends(input_method_dependency).
        csv_file (UploadFile, optional): CSV File to upload.
        Defaults to File().

    Raises:
        HTTPException: BAD_REQUEST
        HTTPException: INTERNAL_SERVER_ERROR

    Returns:
        dict: Successful CSV file upload and list
        of missing teams from the database
    """
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
    """Endpoint for adding the missing teams to the database

    Args:
        new_team (Annotated[NewTeamList, Body, optional):
        New teams to enter to db. Defaults to True)].
        sports_input (InputMethod, optional): Team specifics.
        Defaults to Depends(input_method_dependency).

    Raises:
        HTTPException: INTERNAL_SERVER_ERROR

    Returns:
        dict: Success message
    """
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
    """Runs main algorithm for computing power rankings gathering teams
    and updating their power as needed

    Args:
        iterations (int): Number of runs for the algorithm
        sport_input (InputMethod, optional):
        The specific key for db interactions.
        Defaults to Depends(input_method_dependency).

    Raises:
        HTTPException: Internal Server Error

    Returns:
        dict: The task id for checking if a task is running
        and a message that the task has started
    """
    try:
        level_key = [
            sport_input.sport_type,
            sport_input.gender,
            sport_input.level
        ]
        task = run_main_algorithm.delay(
            level_key=level_key,
            iterations=iterations
        )
        return {"task_id": task.id, "message": "Task has been started."}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        ) from exc


@router.post(
    "/calc_z_scores/",
    tags=["Admin"],
    dependencies=[Depends(AdminServices.get_current_admin)],
    description="Calculates z Scores"
)
async def calc_z_scores(
    sport_input: InputMethod = Depends(input_method_dependency)
):
    """Calculates the z scores and updates it as more games are played
    also it changes past games. This should be ran after the main algorithm
    has been ran.

    Args:
        sport_input (InputMethod, optional):
        The specific key for db interactions.
        Defaults to Depends(input_method_dependency).

    Raises:
        HTTPException: Internal Server Error
    """
    try:
        level_key = (
            sport_input.sport_type,
            sport_input.gender,
            sport_input.level
        )
        team_services = admin_team_class(level_key)
        await team_services.calculate_z_scores()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        ) from exc


@router.get(
    "/task-status/{task_id}",
    tags=["Admin"],
    dependencies=[Depends(AdminServices.get_current_admin)],
    description="Checks Status of Task"
)
async def task_checker(task_id: str):
    """Checks the status of background task (main algorithm)
    to give the user an update on the status of the task

    Args:
        task_id (str): Task id value

    Raises:
        HTTPException: Internal Server Error

    Returns:
        dict: returns the task id and the state of that specific
        task.
    """
    try:
        task_result = AsyncResult(task_id, app=celery)
        state = task_result.state

        result = {
            "task_id": task_id,
            "status": state,
        }

        if state == states.SUCCESS:
            result["result"] = task_result.get()
        elif state == states.FAILURE:
            result["error"] = str(task_result.result)
        elif state == states.PENDING:
            if not task_result.ready():
                result["status"] = "PENDING"
                result["message"] = "Task is in queue or processing"
            else:
                result["status"] = "NOT_FOUND"
                result["message"] = "Task not found"
        
        return result
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        ) from exc


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
    """Updates teams information if in the case a game has incorrect
    scores input. This updates the teams in the db as well as the 
    stored csv file.

    Args:
        update_data (UpdateTeamsData, optional): 
        Required information for updating the teams.
        Defaults to Depends(update_method).
        sport_input (InputMethod, optional):
        The specific key for db interactions.
        Defaults to Depends(input_method_dependency).

    Returns:
        dict: The status and a message of success
    """
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
    """Needs to be implemented
    """
    pass
