"""Shared MongoDB connection pool and collection index definitions."""

import os
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING, IndexModel


def _mongo_uri() -> str:
    return os.getenv("MONGO_URI") or (
        f"mongodb+srv://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASS')}@"
        "sports-cluster.mx1mo.mongodb.net/"
        "?retryWrites=true&w=majority&appName=Sports-Cluster"
    )


def _pool_size(name: str, default: int) -> int:
    try:
        return max(1, int(os.getenv(name, str(default))))
    except ValueError:
        return default


mongo_client = AsyncIOMotorClient(
    _mongo_uri(),
    maxPoolSize=_pool_size("MONGO_MAX_POOL_SIZE", 50),
    minPoolSize=0,
    maxIdleTimeMS=60_000,
)
sports_database = mongo_client["sports_data"]
admin_database = mongo_client["admin_details"]

DATASET_COLLECTIONS = (
    "temp2",
    "csv_files",
    "flagged_games",
    "previous_season",
)
DATASET_INDEX_NAME = "uq_dataset_key"
GAME_IDENTITY_INDEX_NAME = "uq_game_identity"
GAME_DATE_INDEX_NAME = "ix_games_dataset_date"
ADMIN_USERNAME_INDEX_NAME = "uq_admin_username"
EXECUTION_HISTORY_INDEX_NAME = "ix_execution_history_process_queued"

_DATASET_KEY = [
    ("sport_type", ASCENDING),
    ("gender", ASCENDING),
    ("level", ASCENDING),
]


def _index_matches(existing: dict[str, Any], expected: IndexModel) -> bool:
    expected_document = expected.document
    return (
        existing.get("key") == list(expected_document["key"].items())
        and bool(existing.get("unique"))
        == bool(expected_document.get("unique"))
        and bool(existing.get("sparse"))
        == bool(expected_document.get("sparse"))
        and existing.get("partialFilterExpression")
        == expected_document.get("partialFilterExpression")
    )


async def _ensure_index(collection: Any, index: IndexModel) -> list[str]:
    index_name = index.document["name"]
    existing = (await collection.index_information()).get(index_name)
    if existing and not _index_matches(existing, index):
        await collection.drop_index(index_name)
    return await collection.create_indexes([index])


async def ensure_database_indexes(
    sports_db: Any = None,
    admin_db: Any = None,
) -> dict[str, list[str]]:
    """Create the indexes used by application query and upsert paths."""
    sports_db = sports_database if sports_db is None else sports_db
    admin_db = admin_database if admin_db is None else admin_db
    created = {}

    for collection_name in DATASET_COLLECTIONS:
        collection = sports_db.get_collection(collection_name)
        created[collection_name] = await _ensure_index(
            collection,
            IndexModel(
                _DATASET_KEY,
                name=DATASET_INDEX_NAME,
                unique=True,
                sparse=True,
            ),
        )

    games_collection = sports_db.get_collection("games")
    created["games"] = []
    created["games"].extend(await _ensure_index(
        games_collection,
        IndexModel(
            [*_DATASET_KEY, ("identity", ASCENDING)],
            name=GAME_IDENTITY_INDEX_NAME,
            unique=True,
        ),
    ))
    created["games"].extend(await _ensure_index(
        games_collection,
        IndexModel(
            [*_DATASET_KEY, ("game_date", ASCENDING)],
            name=GAME_DATE_INDEX_NAME,
        ),
    ))

    created["admin"] = await _ensure_index(
        admin_db.get_collection("admin"),
        IndexModel(
            [("username", ASCENDING)],
            name=ADMIN_USERNAME_INDEX_NAME,
            unique=True,
            sparse=True,
        ),
    )
    created["execution_history"] = await _ensure_index(
        admin_db.get_collection("execution_history"),
        IndexModel(
            [("process", ASCENDING), ("queued_at", DESCENDING)],
            name=EXECUTION_HISTORY_INDEX_NAME,
        ),
    )
    return created


def close_mongo_client() -> None:
    mongo_client.close()
