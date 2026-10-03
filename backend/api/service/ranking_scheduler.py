"""Coordinate debounced, weekly, and manual ranking jobs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging
import os
from typing import Any, Iterable
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from api.config.constants import LEVEL_CONSTANTS
from api.database import sports_database
from api.service.execution_history import (
    ALGORITHM_PROCESS,
    execution_error_detail,
    record_execution,
    update_execution_status,
)


logger = logging.getLogger(__name__)

AUTOMATIC_TRIGGER = "automatic"
MANUAL_TRIGGER = "manual"
WEEKLY_TRIGGER = "weekly"

_RANKING_GUARD_PREFIX = "ppr:ranking-job"
_RELEASE_GUARD_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
end
return 0
"""


@dataclass(frozen=True)
class RankingEnqueueResult:
    queued: bool
    task_id: str | None = None
    reason: str | None = None


def _env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return min(maximum, max(minimum, value))


def automatic_iterations() -> int:
    return _env_int("AUTO_RANKING_ITERATIONS", 1, 1, 100)


def debounce_seconds() -> int:
    return _env_int("RANKING_DEBOUNCE_SECONDS", 600, 0, 86_400)


def guard_seconds() -> int:
    return _env_int("RANKING_JOB_GUARD_SECONDS", 3_600, 300, 86_400)


def ranking_timezone() -> ZoneInfo:
    timezone_name = os.getenv("RANKING_TIMEZONE", "America/Denver").strip()
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise RuntimeError(
            f"RANKING_TIMEZONE is not a valid IANA timezone: {timezone_name}"
        ) from exc


def normalize_level_key(level_key: Iterable[Any]) -> tuple[str, str, str]:
    key = tuple(str(getattr(value, "value", value)) for value in level_key)
    if len(key) != 3 or key not in LEVEL_CONSTANTS:
        raise ValueError(f"Unknown ranking dataset: {key}")
    return key


def dataset_query(level_key: Iterable[Any]) -> dict[str, str]:
    sport_type, gender, level = normalize_level_key(level_key)
    return {
        "sport_type": sport_type,
        "gender": gender,
        "level": level,
    }


def stale_ranking_update(
    *,
    now: datetime | None = None,
    extra_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the atomic update applied after ranking inputs change."""
    requested_at = now or datetime.now(timezone.utc)
    fields = {
        "rankings_stale": True,
        "ranking_status": "stale",
        "ranking_requested_at": requested_at,
        "ranking_error": None,
    }
    fields.update(extra_fields or {})
    return {
        "$set": fields,
        "$inc": {"games_revision": 1},
    }


async def mark_dataset_stale(
    collection: Any,
    query: dict[str, Any],
    *,
    now: datetime | None = None,
    extra_fields: dict[str, Any] | None = None,
) -> Any:
    return await collection.update_one(
        query,
        stale_ranking_update(now=now, extra_fields=extra_fields),
    )


async def initialize_ranking_state() -> None:
    """Backfill scheduler fields without disturbing existing rankings."""
    collection = sports_database.get_collection("temp2")
    await collection.update_many(
        {},
        [{
            "$set": {
                "games_revision": {"$ifNull": ["$games_revision", 0]},
                "ranked_revision": {"$ifNull": ["$ranked_revision", 0]},
                "rankings_stale": {"$ifNull": ["$rankings_stale", False]},
                "ranking_status": {
                    "$ifNull": [
                        "$ranking_status",
                        {
                            "$cond": [
                                {"$eq": ["$rankings_stale", True]},
                                "stale",
                                "current",
                            ]
                        },
                    ]
                },
            }
        }],
    )


def weekly_snapshot_key(now: datetime | None = None) -> str:
    """Return the local ISO week used to make Sunday snapshots idempotent."""
    captured_at = now or datetime.now(timezone.utc)
    if captured_at.tzinfo is None:
        captured_at = captured_at.replace(tzinfo=timezone.utc)
    iso_year, iso_week, _ = captured_at.astimezone(
        ranking_timezone()
    ).isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


async def snapshot_weekly_last_ranks(
    *,
    now: datetime | None = None,
) -> int:
    """Copy current ranks into last_rank at most once per local week."""
    captured_at = now or datetime.now(timezone.utc)
    if captured_at.tzinfo is None:
        captured_at = captured_at.replace(tzinfo=timezone.utc)
    captured_at = captured_at.astimezone(timezone.utc)
    week_key = weekly_snapshot_key(captured_at)
    collection = sports_database.get_collection("temp2")
    result = await collection.update_many(
        {
            "teams.0": {"$exists": True},
            "last_rank_snapshot_week": {"$ne": week_key},
        },
        [{
            "$set": {
                "teams": {
                    "$map": {
                        "input": "$teams",
                        "as": "team",
                        "in": {
                            "$mergeObjects": [
                                "$$team",
                                {
                                    "last_rank": {
                                        "$ifNull": ["$$team.overall_rank", 0]
                                    }
                                },
                            ]
                        },
                    }
                },
                "last_rank_snapshot_week": week_key,
                "last_rank_snapshot_at": captured_at,
            }
        }],
    )
    return int(result.modified_count)


def _guard_key(level_key: Iterable[Any]) -> str:
    return f"{_RANKING_GUARD_PREFIX}:{':'.join(normalize_level_key(level_key))}"


async def release_ranking_guard(
    redis: Any,
    level_key: Iterable[Any],
    task_id: str,
) -> None:
    await redis.eval(
        _RELEASE_GUARD_SCRIPT,
        1,
        _guard_key(level_key),
        task_id,
    )


async def mark_no_games(level_key: Iterable[Any]) -> None:
    collection = sports_database.get_collection("temp2")
    constant = LEVEL_CONSTANTS[normalize_level_key(level_key)]
    document = await collection.find_one(
        {"_id": constant["_id"]},
        {"games_revision": 1},
    )
    if not document:
        return
    revision = int(document.get("games_revision", 0))
    await collection.update_one(
        {"_id": constant["_id"]},
        {"$set": {
            "rankings_stale": False,
            "ranked_revision": revision,
            "ranking_status": "no_games",
            "ranking_completed_at": datetime.now(timezone.utc),
            "ranking_error": None,
        }},
    )


async def enqueue_ranking_job(
    redis: Any,
    level_key: Iterable[Any],
    *,
    iterations: int | None = None,
    trigger: str = MANUAL_TRIGGER,
) -> RankingEnqueueResult:
    """Queue one full ranking pipeline while suppressing dataset duplicates."""
    key = normalize_level_key(level_key)
    iterations = automatic_iterations() if iterations is None else iterations
    if iterations < 1 or iterations > 100:
        raise ValueError("Iterations must be between 1 and 100")

    games = sports_database.get_collection("games")
    if not await games.find_one(dataset_query(key), {"_id": 1}):
        await mark_no_games(key)
        return RankingEnqueueResult(queued=False, reason="no_games")

    task_id = uuid4().hex
    guard_acquired = await redis.set(
        _guard_key(key),
        task_id,
        ex=guard_seconds(),
        nx=True,
    )
    if not guard_acquired:
        return RankingEnqueueResult(queued=False, reason="already_active")

    collection = sports_database.get_collection("temp2")
    constant = LEVEL_CONSTANTS[key]
    try:
        await record_execution(
            task_id,
            ALGORITHM_PROCESS,
            *key,
            iterations=iterations,
            trigger=trigger,
        )
        await collection.update_one(
            {"_id": constant["_id"]},
            {"$set": {
                "ranking_status": "queued",
                "ranking_task_id": task_id,
                "ranking_trigger": trigger,
                "ranking_iterations": iterations,
                "ranking_error": None,
            }},
        )
        job = await redis.enqueue_job(
            "run_main_algorithm",
            key,
            iterations,
            trigger,
            _job_id=task_id,
        )
        if job is None:
            raise RuntimeError("The ranking job could not be queued")
    except Exception as exc:
        error = execution_error_detail(exc)
        await update_execution_status(task_id, "failed", error=error)
        await collection.update_one(
            {"_id": constant["_id"]},
            {"$set": {
                "rankings_stale": True,
                "ranking_status": "failed",
                "ranking_error": error,
                "ranking_requested_at": datetime.now(timezone.utc),
            }},
        )
        try:
            await release_ranking_guard(redis, key, task_id)
        except Exception:
            logger.exception("Failed to release ranking guard for %s", key)
        raise

    return RankingEnqueueResult(queued=True, task_id=task_id)


async def mark_ranking_started(
    level_key: Iterable[Any],
    task_id: str,
    trigger: str,
) -> int:
    key = normalize_level_key(level_key)
    collection = sports_database.get_collection("temp2")
    constant = LEVEL_CONSTANTS[key]
    await collection.update_one(
        {"_id": constant["_id"], "games_revision": {"$exists": False}},
        {"$set": {"games_revision": 0}},
    )
    document = await collection.find_one(
        {"_id": constant["_id"]},
        {"games_revision": 1},
    )
    if not document:
        raise RuntimeError(f"Ranking dataset does not exist: {key}")
    revision = int(document.get("games_revision", 0))
    await collection.update_one(
        {"_id": constant["_id"]},
        {"$set": {
            "ranking_status": "in_progress",
            "ranking_task_id": task_id,
            "ranking_trigger": trigger,
            "ranking_started_at": datetime.now(timezone.utc),
            "ranking_error": None,
        }},
    )
    return revision


async def mark_ranking_complete(
    level_key: Iterable[Any],
    task_id: str,
    started_revision: int,
) -> bool:
    """Mark current only if no ranking input changed during calculation."""
    key = normalize_level_key(level_key)
    collection = sports_database.get_collection("temp2")
    constant = LEVEL_CONSTANTS[key]
    completed_at = datetime.now(timezone.utc)
    result = await collection.update_one(
        {
            "_id": constant["_id"],
            "games_revision": started_revision,
            "ranking_task_id": task_id,
        },
        {"$set": {
            "rankings_stale": False,
            "ranked_revision": started_revision,
            "ranking_status": "current",
            "ranking_completed_at": completed_at,
            "ranking_error": None,
        }},
    )
    if result.matched_count:
        return True

    await collection.update_one(
        {"_id": constant["_id"], "ranking_task_id": task_id},
        {"$set": {
            "rankings_stale": True,
            "ranking_status": "stale",
            "ranking_error": None,
        }},
    )
    return False


async def mark_ranking_failed(
    level_key: Iterable[Any],
    task_id: str,
    error: dict[str, str],
) -> None:
    key = normalize_level_key(level_key)
    collection = sports_database.get_collection("temp2")
    constant = LEVEL_CONSTANTS[key]
    await collection.update_one(
        {"_id": constant["_id"], "ranking_task_id": task_id},
        {"$set": {
            "rankings_stale": True,
            "ranking_status": "failed",
            "ranking_error": error,
            "ranking_requested_at": datetime.now(timezone.utc),
        }},
    )


async def _dispatch_stale_rankings(
    redis: Any,
    *,
    trigger: str,
    quiet_before: datetime | None,
) -> dict[str, int]:
    collection = sports_database.get_collection("temp2")
    query: dict[str, Any] = {"rankings_stale": True}
    if quiet_before is not None:
        query["$or"] = [
            {"ranking_requested_at": {"$lte": quiet_before}},
            {"ranking_requested_at": {"$exists": False}},
        ]
    cursor = collection.find(
        query,
        {"sport_type": 1, "gender": 1, "level": 1},
    )
    documents = await cursor.to_list(length=None)
    queued = active = no_games = failed = 0
    for document in documents:
        level_key = (
            document.get("sport_type"),
            document.get("gender"),
            document.get("level"),
        )
        if level_key not in LEVEL_CONSTANTS:
            logger.warning("Skipping unknown stale ranking dataset: %s", level_key)
            continue
        try:
            result = await enqueue_ranking_job(
                redis,
                level_key,
                trigger=trigger,
            )
        except Exception:
            failed += 1
            logger.exception("Failed to queue %s ranking for %s", trigger, level_key)
            continue
        if result.queued:
            queued += 1
        elif result.reason == "already_active":
            active += 1
        elif result.reason == "no_games":
            no_games += 1
    return {
        "queued": queued,
        "already_active": active,
        "no_games": no_games,
        "failed": failed,
    }


async def dispatch_due_rankings(ctx: dict[str, Any]) -> dict[str, int]:
    quiet_before = datetime.now(timezone.utc) - timedelta(
        seconds=debounce_seconds()
    )
    return await _dispatch_stale_rankings(
        ctx["redis"],
        trigger=AUTOMATIC_TRIGGER,
        quiet_before=quiet_before,
    )


async def weekly_ranking_catchup(ctx: dict[str, Any]) -> dict[str, int]:
    snapshots = await snapshot_weekly_last_ranks()
    result = await _dispatch_stale_rankings(
        ctx["redis"],
        trigger=WEEKLY_TRIGGER,
        quiet_before=None,
    )
    return {**result, "last_rank_snapshots": snapshots}
