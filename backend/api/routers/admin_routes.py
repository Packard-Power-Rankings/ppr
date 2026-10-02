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
import os
import traceback
from uuid import uuid4
from typing import Tuple, List, Dict
# from celery.result import AsyncResult
# from celery import states
from arq.connections import create_pool
from arq.jobs import Job, JobStatus
from bson import ObjectId
from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
    HTTPException,
    Query,
    status,
    Response,
    Request
)
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordRequestForm
from api.service.tasks import run_main_algorithm, calc_z_score
from api.schemas.items import (
    InputMethod,
    NewGameData,
    NewTeamData,
    UpdateTeamsData,
    UpdateTeamInfo,
    LogoutResponse,
    FlaggedGame,
    SetupAdminRequest,
    Token
)
from api.service.admin_teams import AdminTeamsService
from api.service.archive_service import ArchiveService
from api.service.admin_service import AdminServices
from api.service.execution_history import (
    ALGORITHM_PROCESS,
    Z_SCORE_PROCESS,
    execution_error_detail,
    recent_execution_history,
    record_execution,
    update_execution_status,
)
from api.service.team_ingestion import TeamFileValidationError
# from api.service.celery import celery
from api.config.constants import (
    DIVISION_FOOTBALL,
    DIVISION_BASKETBALL,
    FOOTBALL_COLLEGE_CONF,
    CONFERENCE_CB,
    STATES
)
from api.config.redis import get_redis_settings

router = APIRouter()
admin_service = AdminServices()
archive_service = ArchiveService()
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


@router.post("/token/", response_model=Token)
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


@router.post("/setup/admin/")
async def setup_admin_account(
    request: Request,
    setup_request: SetupAdminRequest,
    admin_service: AdminServices = Depends()
):
    """One-time endpoint for creating the initial admin user via curl."""
    expected_token = os.getenv("SETUP_TOKEN")
    provided_token = request.headers.get("X-Setup-Token")

    if not expected_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Setup token is not configured"
        )

    if provided_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid setup token"
        )

    admin_id = await admin_service.create_admin(
        setup_request.username,
        setup_request.password
    )
    return {"message": "Admin created", "id": admin_id}


def require_admin():
    """Dependency for protected routes that checks auth token"""
    async def wrapper(request: Request):
        return await AdminServices().get_current_user(request)
    return Depends(wrapper)


@router.get(
    "/archive-season/status",
    dependencies=[require_admin()],
    description="Check whether a complete current-season archive exists",
)
async def archive_season_status(
    year: int | None = Query(default=None, ge=2000, le=9999),
):
    return archive_service.archive_status(year)


def _archive_dataset_key(sports_input: InputMethod) -> tuple[str, str, str]:
    return (
        sports_input.sport_type.value,
        sports_input.gender.value,
        sports_input.level.value,
    )


@router.get(
    "/archive-season/status/selected",
    dependencies=[require_admin()],
    description="Check whether one sport dataset is archived for the season",
)
async def selected_archive_season_status(
    year: int | None = Query(default=None, ge=2000, le=9999),
    sports_input: InputMethod = Depends(),
):
    return archive_service.archive_status(
        year,
        _archive_dataset_key(sports_input),
    )


@router.post(
    "/archive-season/all/",
    dependencies=[require_admin()],
    description="Archive every current sport dataset as public static pages",
)
async def archive_all_sports(
    year: int | None = Query(default=None, ge=2000, le=9999),
    overwrite: bool = Query(default=False),
):
    return await archive_service.archive_current_season(year, overwrite)


@router.post(
    "/archive-season/selected/",
    dependencies=[require_admin()],
    description="Archive one sport dataset while retaining other archived datasets",
)
async def archive_selected_sport(
    year: int | None = Query(default=None, ge=2000, le=9999),
    overwrite: bool = Query(default=False),
    sports_input: InputMethod = Depends(),
):
    return await archive_service.archive_current_season(
        year,
        overwrite,
        _archive_dataset_key(sports_input),
    )


@router.post(
    "/archive-season/",
    dependencies=[require_admin()],
    include_in_schema=False,
)
async def archive_season_legacy(
    year: int | None = Query(default=None, ge=2000, le=9999),
    overwrite: bool = Query(default=False),
):
    """Compatibility route for clients that archive all sports."""
    return await archive_service.archive_current_season(year, overwrite)


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


async def _store_uploaded_games(
    csv_file: UploadFile = File(),
    sports_input: InputMethod = Depends(),
):
    level_key = (
        sports_input.sport_type,
        sports_input.gender,
        sports_input.level,
    )


@router.post(
    "/teams/upload/",
    dependencies=[require_admin()],
    description="Validate and import team metadata from a CSV file",
)
async def upload_teams(
    csv_file: UploadFile = File(),
    sports_input: InputMethod = Depends(),
):
    level_key = (
        sports_input.sport_type,
        sports_input.gender,
        sports_input.level,
    )
    team_services = admin_team_class(level_key)
    try:
        return await team_services.import_team_csv(
            csv_file.filename or "teams.csv",
            await csv_file.read(),
        )
    except TeamFileValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Team data file format is not correct",
                "errors": exc.errors,
            },
        ) from exc
    team_services = admin_team_class(level_key)
    return await team_services.store_csv(
        sports_input.sport_type,
        sports_input.gender,
        sports_input.level,
        csv_file,
    )


@router.post(
    "/games/upload/",
    dependencies=[require_admin()],
    description="Validate and upload a game CSV",
)
async def upload_games(
    csv_file: UploadFile = File(),
    sports_input: InputMethod = Depends(),
):
    return await _store_uploaded_games(csv_file, sports_input)


@router.post(
    "/upload_csv/",
    dependencies=[require_admin()],
    include_in_schema=False,
)
async def upload_csv_legacy(
    csv_file: UploadFile = File(),
    sports_input: InputMethod = Depends(),
):
    """Compatibility route for older clients."""
    return await _store_uploaded_games(csv_file, sports_input)


@router.post(
    "/games/",
    dependencies=[require_admin()],
    description="Validate and add one game",
)
async def add_game(
    game: NewGameData,
    sports_input: InputMethod = Depends(),
):
    level_key = (
        sports_input.sport_type,
        sports_input.gender,
        sports_input.level,
    )
    team_services = admin_team_class(level_key)
    return await team_services.store_game(
        sports_input.sport_type,
        sports_input.gender,
        sports_input.level,
        game.model_dump(),
    )


@router.post(
    "/add_teams/",
    dependencies=[require_admin()],
    description="Add team metadata with canonical team IDs"
)
async def add_missing_teams(
    new_team: List[NewTeamData],
    sports_input: InputMethod = Depends()
):
    """Add manually entered team metadata to the selected dataset.

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
        level_key = (
            sports_input.sport_type,
            sports_input.gender,
            sports_input.level
        )
        team_services = admin_team_class(level_key)
        results = await team_services.add_teams_to_db([
            team.model_dump() for team in new_team
        ])
        return results
    except HTTPException:
        raise
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Error"
        ) from exc


@router.get(
    "/export_teams/",
    dependencies=[require_admin()],
    description="Export all stored team fields for one dataset",
)
async def export_teams(sports_input: InputMethod = Depends()):
    level_key = (
        sports_input.sport_type.value,
        sports_input.gender.value,
        sports_input.level.value,
    )
    teams = await admin_team_class(level_key).get_all_teams()
    return {"teams": jsonable_encoder(teams, custom_encoder={ObjectId: str})}


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
    if iterations < 1 or iterations > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Iterations must be between 1 and 100",
        )
    task_id = uuid4().hex
    level_key = (
        sport_input.sport_type.value,
        sport_input.gender.value,
        sport_input.level.value,
    )
    await record_execution(
        task_id,
        ALGORITHM_PROCESS,
        *level_key,
        iterations=iterations,
    )
    try:
        redis = await create_pool(get_redis_settings())
        job = await redis.enqueue_job(
            "run_main_algorithm",
            level_key,
            iterations,
            _job_id=task_id,
        )
        if job is None:
            raise RuntimeError("The algorithm job could not be queued")
        return {"task_id": task_id, "message": "Task has been started."}
    except Exception as exc:
        await update_execution_status(
            task_id,
            "failed",
            error=execution_error_detail(exc),
        )
        raise HTTPException(
            status_code=500, detail="Internal Server Error") from exc


@router.post(
    "/calc_z_scores/",
    dependencies=[require_admin()],
    description="Calculates z Scores"
)
async def calc_z_scores(
    sport_input: InputMethod = Depends()
):
    task_id = uuid4().hex
    level_key = (
        sport_input.sport_type.value,
        sport_input.gender.value,
        sport_input.level.value,
    )
    await record_execution(
        task_id,
        Z_SCORE_PROCESS,
        *level_key,
    )
    try:
        redis = await create_pool(get_redis_settings())
        job = await redis.enqueue_job(
            "calc_z_score",
            level_key,
            _job_id=task_id,
        )
        if job is None:
            raise RuntimeError("The z-score job could not be queued")
        return {"task_id": task_id, "message": "Task has been started."}
    except Exception as exc:
        await update_execution_status(
            task_id,
            "failed",
            error=execution_error_detail(exc),
        )
        raise HTTPException(
            status_code=500, detail="Internal Server Error") from exc


@router.get(
    "/execution-history/",
    dependencies=[require_admin()],
    description="Returns the five most recent algorithm and z-score executions",
)
async def get_execution_history():
    try:
        history = await recent_execution_history()
        redis = await create_pool(get_redis_settings())
        history_changed = False
        for records in history.values():
            for record in records:
                status_needs_refresh = record.get("status") in {
                    "queued",
                    "in_progress",
                }
                error_needs_backfill = (
                    record.get("status") == "failed"
                    and not record.get("error")
                )
                if not status_needs_refresh and not error_needs_backfill:
                    continue
                job = Job(job_id=record["task_id"], redis=redis)
                job_status = await job.status()
                if job_status == JobStatus.in_progress:
                    if record.get("status") != "in_progress":
                        await update_execution_status(
                            record["task_id"],
                            "in_progress",
                        )
                        history_changed = True
                elif job_status == JobStatus.complete:
                    try:
                        result = await job.result_info()
                    except Exception as result_error:
                        await update_execution_status(
                            record["task_id"],
                            "failed",
                            error={
                                "type": "WorkerResultUnreadable",
                                "message": (
                                    "The stored worker exception could not be "
                                    "read. Run the job again to capture its "
                                    "full failure details. Original read error: "
                                    f"{type(result_error).__name__}."
                                ),
                                "location": "ARQ result store",
                            },
                        )
                        history_changed = True
                        continue
                    succeeded = bool(result and result.success)
                    await update_execution_status(
                        record["task_id"],
                        "complete" if succeeded else "failed",
                        started_at=result.start_time if result else None,
                        finished_at=result.finish_time if result else None,
                        error=(
                            execution_error_detail(result.result)
                            if result and not succeeded
                            else None
                        ),
                    )
                    history_changed = True
                elif job_status == JobStatus.not_found:
                    await update_execution_status(
                        record["task_id"],
                        "failed",
                        error={
                            "type": "WorkerResultUnavailable",
                            "message": (
                                "The worker result expired or the job ended "
                                "before failure details were recorded."
                            ),
                            "location": "ARQ result store",
                        },
                    )
                    history_changed = True

        return await recent_execution_history() if history_changed else history
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail="Internal Server Error") from exc


@router.get(
    "/task-status/{task_id}",
    dependencies=[require_admin()],
    description="Checks Status of Task"
)
async def task_checker(task_id: str):
    try:
        redis = await create_pool(get_redis_settings())
        job_info = Job(job_id=task_id, redis=redis)
        return {
            "info": await job_info.info(),
            "status": await job_info.status()
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail="Internal Server Error") from exc


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
        update_data.date,
        update_data.game_id
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


@router.put(
    "/update-team/{team_id}",
    dependencies=[require_admin()],
    description="Update Team Information"
)
async def update_team_info(
    team_id: int,
    team_info: UpdateTeamInfo,
    sport_input: InputMethod = Depends()
):
    team_service = admin_team_class(
        (
            sport_input.sport_type,
            sport_input.gender,
            sport_input.level
        )
    )
    return await team_service.update_team_info(team_id, team_info.model_dump())


@router.delete(
    "/clear-season/",
    dependencies=[require_admin()],
    description="Reset Selected Sport Season"
)
async def clear_season(
    sport_input: InputMethod = Depends()
):
    """Reset the selected sport season without modifying public archives."""
    team_service = admin_team_class(
        (
            sport_input.sport_type,
            sport_input.gender,
            sport_input.level
        )
    )
    return await team_service.clear_season()


@router.delete(
    "/reset-all-sports/",
    dependencies=[require_admin()],
    description="Reset All Sports"
)
async def reset_all_sports():
    """Reset every current sport dataset without modifying public archives."""
    team_service = admin_team_class(("football", "mens", "high_school"))
    return await team_service.reset_all_sports()


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
