"""Persist recent administrative algorithm execution records."""

from datetime import datetime, timezone
from pathlib import Path
import traceback
from typing import Any

from api.database import admin_database

ALGORITHM_PROCESS = "algorithm"
Z_SCORE_PROCESS = "z_scores"
HISTORY_LIMIT = 5
PRUNE_BATCH_SIZE = 500


def _history_collection() -> Any:
    return admin_database.get_collection("execution_history")


def _iso_timestamp(value: datetime | str | None = None) -> str:
    if isinstance(value, str):
        return value
    timestamp = value or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def execution_error_detail(error: Any) -> dict[str, str]:
    """Build a concise, serializable failure summary for administrators."""
    if isinstance(error, BaseException):
        frames = traceback.extract_tb(error.__traceback__)
        location = "Background worker"
        if frames:
            frame = frames[-1]
            location = f"{Path(frame.filename).name}:{frame.lineno} in {frame.name}"
        error_type = type(error).__name__
        message = str(error).strip() or "No exception message was provided."
    else:
        error_type = "WorkerError"
        message = str(error).strip() or "No exception message was provided."
        location = "Background worker"
    return {
        "type": error_type,
        "message": message,
        "location": location,
    }


async def _prune_process_history(collection: Any, process: str) -> None:
    cursor = collection.find(
        {"process": process},
        {
            "_id": 1,
            "sport_type": 1,
            "gender": 1,
            "level": 1,
            "queued_at": 1,
        },
    ).sort("queued_at", -1)
    dataset_counts: dict[tuple[Any, Any, Any], int] = {}

    while True:
        records = await cursor.to_list(length=PRUNE_BATCH_SIZE)
        if not records:
            break

        obsolete_ids = []
        for record in records:
            dataset = (
                record.get("level"),
                record.get("gender"),
                record.get("sport_type"),
            )
            dataset_counts[dataset] = dataset_counts.get(dataset, 0) + 1
            if dataset_counts[dataset] > HISTORY_LIMIT:
                obsolete_ids.append(record["_id"])

        if obsolete_ids:
            await collection.delete_many({"_id": {"$in": obsolete_ids}})


async def prune_execution_history() -> None:
    """Delete records older than the most recent limit for each process."""
    collection = _history_collection()
    for process in (ALGORITHM_PROCESS, Z_SCORE_PROCESS):
        await _prune_process_history(collection, process)


async def record_execution(
    task_id: str,
    process: str,
    sport_type: str,
    gender: str,
    level: str,
    iterations: int | None = None,
) -> None:
    queued_at = _iso_timestamp()
    collection = _history_collection()
    await collection.insert_one({
        "_id": task_id,
        "task_id": task_id,
        "process": process,
        "sport_type": sport_type,
        "gender": gender,
        "level": level,
        "iterations": iterations,
        "status": "queued",
        "queued_at": queued_at,
        "started_at": None,
        "finished_at": None,
        "error": None,
        "updated_at": queued_at,
    })
    await _prune_process_history(collection, process)


async def update_execution_status(
    task_id: str,
    status: str,
    *,
    started_at: datetime | str | None = None,
    finished_at: datetime | str | None = None,
    error: dict[str, str] | None = None,
) -> None:
    updated_at = _iso_timestamp(finished_at or started_at)
    update = {"status": status, "updated_at": updated_at}
    if status == "in_progress":
        update["started_at"] = _iso_timestamp(started_at)
        update["error"] = None
    elif status in {"complete", "failed"}:
        if started_at is not None:
            update["started_at"] = _iso_timestamp(started_at)
        update["finished_at"] = _iso_timestamp(finished_at)
        update["error"] = error if status == "failed" else None

    await _history_collection().update_one(
        {"_id": task_id},
        {"$set": update},
    )


async def recent_execution_history() -> dict[str, list[dict]]:
    await prune_execution_history()
    collection = _history_collection()
    history = {}
    for process in (ALGORITHM_PROCESS, Z_SCORE_PROCESS):
        cursor = collection.find(
            {"process": process},
            {"_id": 0},
        ).sort("queued_at", -1)
        history[process] = await cursor.to_list(length=None)
    return history
