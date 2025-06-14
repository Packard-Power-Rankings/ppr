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
from typing import Tuple, List, Dict
# from celery.result import AsyncResult
# from celery import states
from arq.connections import create_pool, RedisSettings
from arq.jobs import Job
from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
    HTTPException,
    status,
    Response,
    Request
)
from fastapi.security import OAuth2PasswordRequestForm
from api.service.tasks import run_main_algorithm, calc_z_score
from api.schemas.items import (
    InputMethod,
    UpdateTeamsData,
    LoginResponse,
    LogoutResponse,
    FlaggedGame
)
from api.service.admin_teams import AdminTeamsService
from api.service.admin_service import AdminServices
# from api.service.celery import celery
from api.config.constants import (
    DIVISION_FOOTBALL,
    DIVISION_BASKETBALL,
    FOOTBALL_COLLEGE_CONF,
    CONFERENCE_CB,
    STATES
)

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


@router.post("/token/", response_model=LoginResponse)
async def login_generate_token(
    response: Response,
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
    return await admin_service.login(form_data, response)


@router.post("/logout/", response_model=LogoutResponse)
async def logout(
    response: Response,
    admin_service: AdminServices = Depends()
):
    return await admin_service.logout(response)


@router.get("/validate-token/")
async def validate_token(
    request: Request,
    admin_service: AdminServices = Depends()
):
    return await admin_service.validate_token(request)


def require_admin():
    """Dependency for protected routes that checks cookie auth"""
    async def wrapper(request: Request):
        return await AdminServices().get_current_user(request)
    return Depends(wrapper)


def dict_to_list(data_dict):
    return [{"id": k, "name": v} for k, v in data_dict.items() if v is not None]

@router.get(
    '/sports/',
    dependencies=[require_admin()],
    description="Gets Division, Conferences, and States"
)
def get_sports_info(
    sports_input: InputMethod = Depends()
):
    return_message = {}

    if sports_input.sport_type == 'football':
        return_message['division'] = dict_to_list(DIVISION_FOOTBALL)
        if sports_input.level == 'college':
            return_message['conference'] = dict_to_list(FOOTBALL_COLLEGE_CONF)
    else:
        return_message['division'] = dict_to_list(DIVISION_BASKETBALL)
        if sports_input.level == 'college':
            return_message['conference'] = dict_to_list(CONFERENCE_CB)

    return_message["states"] = dict_to_list(STATES)

    return return_message


@router.post(
    "/upload_csv/",
    dependencies=[require_admin()],
    description="Adds CSV File and Finds Missing Teams"
)
async def upload_csv(
    csv_file: UploadFile = File(),
    sports_input: InputMethod = Depends(),
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
        results = await team_services.store_csv(
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
    dependencies=[require_admin()],
    description="Adds Missing Teams To Database"
)
async def add_missing_teams(
    new_team: List[Dict],
    sports_input: InputMethod = Depends()
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
        # teams = new_team.model_dump()
        level_key = (
                sports_input.sport_type,
                sports_input.gender,
                sports_input.level
        )
        team_services = admin_team_class(level_key)
        results = await team_services.add_teams_to_db(new_team)
        return results
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Error"
        ) from exc


@router.post(
    '/check-teams/',
    dependencies=[require_admin()],
    description="Check Missing Teams in DB"
)
async def check_for_missing_teams(
    teams: List[str],
    sports_input: InputMethod = Depends()
):
    level_key = (
                sports_input.sport_type,
                sports_input.gender,
                sports_input.level
        )
    team_services = admin_team_class(level_key)
    results = await team_services.find_missing_teams(teams)
    return {"missing_teams": results}


@router.post(
    "/run_algorithm/{iterations}",
    dependencies=[require_admin()],
    description="Runs Main Algorithm"
)
async def main_algorithm_exc(
    iterations: int,
    sport_input: InputMethod = Depends()
):
    try:
        redis = await create_pool(RedisSettings(host="redis", port=6379))
        job = await redis.enqueue_job(
            "run_main_algorithm",
            (sport_input.sport_type, sport_input.gender, sport_input.level),
            iterations
        )
        return {"task_id": job.job_id, "message": "Task has been started."}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal Server Error") from exc


@router.post(
    "/calc_z_scores/",
    dependencies=[require_admin()],
    description="Calculates z Scores"
)
async def calc_z_scores(
    sport_input: InputMethod = Depends()
):
    try:
        redis = await create_pool(RedisSettings(host="redis", port=6379))
        job = await redis.enqueue_job(
            "calc_z_score",
            (sport_input.sport_type, sport_input.gender, sport_input.level)
        )
        return {"task_id": job.job_id, "message": "Task has been started."}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal Server Error") from exc


@router.get(
    "/task-status/{task_id}",
    dependencies=[require_admin()],
    description="Checks Status of Task"
)
async def task_checker(task_id: str):
    try:
        redis = await create_pool(RedisSettings(host="redis", port=6379))
        job_info = Job(job_id=task_id, redis=redis)
        return {
            "info": await job_info.info(),
            "status": await job_info.status()
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal Server Error") from exc


@router.put(
    "/update-game/",
    dependencies=[require_admin()],
    description="Updates Games and CSV File"
)
async def update_game(
    update_data: UpdateTeamsData = Depends(),
    sport_input: InputMethod = Depends()
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


@router.get(
    '/teams-ids/',
    description='Get team names and ids'
)
async def get_team_names_ids(
    sport_input: InputMethod = Depends()
):
    team_service = admin_team_class(
        (
            sport_input.sport_type,
            sport_input.gender,
            sport_input.level
        )
    )
    return await team_service.get_team_names_and_ids()


@router.put(
    "/update-name/{team_id}/{new_name}",
    dependencies=[require_admin()],
    description="Update Team Name"
)
async def update_team_name(
    team_id: int,
    new_name: str,
    sport_input: InputMethod = Depends()
):
    """
    Update A teams Name
    """
    team_service = admin_team_class(
        (
            sport_input.sport_type,
            sport_input.gender,
            sport_input.level
        )
    )
    return await team_service.update_team_name(team_id, new_name)


@router.delete(
    "/clear-season/",
    dependencies=[require_admin()],
    description="Clears Season"
)
async def clear_season(
    sport_input: InputMethod = Depends()
):
    """
    Moves current season to previous season
    """
    team_service = admin_team_class(
        (
            sport_input.sport_type,
            sport_input.gender,
            sport_input.level
        )
    )
    return await team_service.clear_season()


@router.delete(
    "/delete-game/{team_one}/{team_two}/{game_id:path}/{game_date:path}",
    dependencies=[require_admin()],
    description="Delete A Game"
)
async def delete_game(
    team_one: int,
    team_two: int,
    game_id: str,
    game_date: str,
    sport_input: InputMethod = Depends()
):
    """
    Delete A Game From Database
    """
    team_service = admin_team_class(
        (
            sport_input.sport_type,
            sport_input.gender,
            sport_input.level
        )
    )

    return await team_service.delete_game(team_one, team_two, game_id, game_date)


@router.get(
    '/season-dates/{team_one}/{team_two}',
    dependencies=[require_admin()],
    description="Retrieve game dates of season opp array to delete"
)
async def season_opp_dates(
    team_one: int,
    team_two: int,
    sport_input: InputMethod = Depends()
):
    team_service = admin_team_class(
        (
            sport_input.sport_type,
            sport_input.gender,
            sport_input.level
        )
    )

    return await team_service.find_season_opp_dates(team_one, team_two)


@router.delete(
    "/delete-team/{team_name}/{team_id}/",
    dependencies=[require_admin()],
    description="Delete A Team"
)
async def delete_team(
    team_name: str,
    team_id: int,
    sport_input: InputMethod = Depends()
):
    """
    Delete a team from the database
    """
    team_service = admin_team_class(
        (
            sport_input.sport_type,
            sport_input.gender,
            sport_input.level
        )
    )
    return await team_service.delete_team(team_name, team_id)


@router.post(
    '/flagged-game',
    description="Stores flagged games for admin to fix"
)
async def store_flagged_games(
    game: FlaggedGame,
    sport_input: InputMethod = Depends()
):
    team_service = admin_team_class(
        (
            sport_input.sport_type,
            sport_input.gender,
            sport_input.level
        )
    )

    return await team_service.store_flagged_games(
        game.game_id,
        game.team1_id,
        game.team1_name,
        game.team2_id,
        game.team2_name
    )


@router.delete(
    '/clear-flagged',
    dependencies=[require_admin()],
    description='Clears flagged games once they have been updated'
)
async def clear_flagged_games(
    sport_input: InputMethod = Depends()
):
    team_service = admin_team_class(
        (
            sport_input.sport_type,
            sport_input.gender,
            sport_input.level
        )
    )

    return await team_service.clear_flagged_games()


@router.get(
    '/retrieve-flagged',
    dependencies=[require_admin()],
    description="Retrieves the stored flagged games"
)
async def retrieve_flagged_games(
    sport_input: InputMethod = Depends()
):
    team_service = admin_team_class(
        (
            sport_input.sport_type,
            sport_input.gender,
            sport_input.level
        )
    )
    return await team_service.retrieve_flagged_games()


@router.get(
    '/check-flagged/{game_id:path}',
    description="Checks if game is already flagged"
)
async def check_flagged_game(
    game_id: str,
    sport_input: InputMethod = Depends()
):
    team_service = admin_team_class(
        (
            sport_input.sport_type,
            sport_input.gender,
            sport_input.level
        )
    )

    return await team_service.check_flagged_games(game_id)
