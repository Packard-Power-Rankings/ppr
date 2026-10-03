import logging

from arq import cron

from api.service.admin_teams import AdminTeamsService
from api.config.redis import get_redis_settings
from api.service.execution_history import (
    execution_error_detail,
    update_execution_status,
)
from api.service.ranking_scheduler import (
    dispatch_due_rankings,
    MANUAL_TRIGGER,
    mark_ranking_complete,
    mark_ranking_failed,
    mark_ranking_started,
    ranking_timezone,
    release_ranking_guard,
    weekly_ranking_catchup,
)


logger = logging.getLogger(__name__)


def _current_task_id(ctx) -> str | None:
    """Read the canonical task ID supplied by the ARQ worker context."""
    task_id = ctx.get("job_id") if isinstance(ctx, dict) else None
    return str(task_id) if task_id else None


async def run_main_algorithm(
    ctx,
    level_key,
    iterations: int,
    trigger: str = MANUAL_TRIGGER,
):
    """Runs the main algorithm asynchronously."""
    task_id = _current_task_id(ctx)
    started_revision = None
    try:
        if task_id:
            await update_execution_status(task_id, "in_progress")
            started_revision = await mark_ranking_started(
                level_key,
                task_id,
                trigger,
            )
        team_services = AdminTeamsService(level_key)
        await team_services.run_main_algorithm(iterations)
        if task_id and started_revision is not None:
            await mark_ranking_complete(
                level_key,
                task_id,
                started_revision,
            )
    except Exception as exc:
        error = execution_error_detail(exc)
        if task_id:
            await update_execution_status(
                task_id,
                "failed",
                error=error,
            )
            await mark_ranking_failed(level_key, task_id, error)
        raise RuntimeError(
            f"{error['type']}: {error['message']}"
        ) from exc
    else:
        if task_id:
            await update_execution_status(task_id, "complete")
    finally:
        if task_id and ctx.get("redis") is not None:
            try:
                await release_ranking_guard(ctx["redis"], level_key, task_id)
            except Exception:
                logger.exception(
                    "Failed to release ranking guard for %s",
                    level_key,
                )


async def calc_z_score(ctx, level_key):
    """Calculates Z-score asynchronously."""
    task_id = _current_task_id(ctx)
    if task_id:
        await update_execution_status(task_id, "in_progress")
    try:
        team_services = AdminTeamsService(level_key)
        await team_services.calculate_z_scores()
    except Exception as exc:
        error = execution_error_detail(exc)
        if task_id:
            await update_execution_status(
                task_id,
                "failed",
                error=error,
            )
        raise RuntimeError(
            f"{error['type']}: {error['message']}"
        ) from exc
    if task_id:
        await update_execution_status(task_id, "complete")


class WorkerSettings:
    """Configuration for Arq Worker"""
    functions = [run_main_algorithm, calc_z_score]
    cron_jobs = [
        cron(
            dispatch_due_rankings,
            name="dispatch_due_rankings",
            second=0,
            microsecond=0,
        ),
        cron(
            weekly_ranking_catchup,
            name="weekly_ranking_catchup",
            weekday="sun",
            hour=1,
            minute=0,
            second=0,
            microsecond=0,
        ),
    ]
    redis_settings = get_redis_settings()
    timezone = ranking_timezone()
