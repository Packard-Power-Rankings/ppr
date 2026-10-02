from api.service.admin_teams import AdminTeamsService
from api.config.redis import get_redis_settings
from api.service.execution_history import (
    execution_error_detail,
    update_execution_status,
)


def _current_task_id(ctx) -> str | None:
    """Read the canonical task ID supplied by the ARQ worker context."""
    task_id = ctx.get("job_id") if isinstance(ctx, dict) else None
    return str(task_id) if task_id else None


async def run_main_algorithm(
    ctx,
    level_key,
    iterations: int,
):
    """Runs the main algorithm asynchronously."""
    task_id = _current_task_id(ctx)
    if task_id:
        await update_execution_status(task_id, "in_progress")
    try:
        team_services = AdminTeamsService(level_key)
        await team_services.run_main_algorithm(iterations)
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
    redis_settings = get_redis_settings()
