import pytest

from api.database import (
    ADMIN_USERNAME_INDEX_NAME,
    DATASET_COLLECTIONS,
    DATASET_INDEX_NAME,
    EXECUTION_HISTORY_INDEX_NAME,
    GAME_DATE_INDEX_NAME,
    GAME_IDENTITY_INDEX_NAME,
    ensure_database_indexes,
)


class FakeCollection:
    def __init__(self, existing_indexes=None):
        self.indexes = []
        self.existing_indexes = existing_indexes or {}
        self.dropped_indexes = []

    async def index_information(self):
        return self.existing_indexes

    async def drop_index(self, name):
        self.dropped_indexes.append(name)
        self.existing_indexes.pop(name, None)

    async def create_indexes(self, indexes):
        self.indexes.extend(indexes)
        return [index.document["name"] for index in indexes]


class FakeDatabase:
    def __init__(self, collection_names):
        self.collections = {
            name: FakeCollection() for name in collection_names
        }

    def get_collection(self, name):
        return self.collections[name]


@pytest.mark.asyncio
async def test_ensure_database_indexes_matches_application_queries():
    sports_db = FakeDatabase((*DATASET_COLLECTIONS, "games"))
    admin_db = FakeDatabase(("admin", "execution_history"))

    created = await ensure_database_indexes(sports_db, admin_db)

    assert created == {
        **{name: [DATASET_INDEX_NAME] for name in DATASET_COLLECTIONS},
        "games": [GAME_IDENTITY_INDEX_NAME, GAME_DATE_INDEX_NAME],
        "admin": [ADMIN_USERNAME_INDEX_NAME],
        "execution_history": [EXECUTION_HISTORY_INDEX_NAME],
    }

    for name in DATASET_COLLECTIONS:
        collection = sports_db.collections[name]
        index = collection.indexes[0].document
        assert list(index["key"].items()) == [
            ("sport_type", 1),
            ("gender", 1),
            ("level", 1),
        ]
        assert index["unique"] is True
        assert index["sparse"] is True
        assert "partialFilterExpression" not in index

    game_indexes = [
        index.document for index in sports_db.collections["games"].indexes
    ]
    assert list(game_indexes[0]["key"].items()) == [
        ("sport_type", 1),
        ("gender", 1),
        ("level", 1),
        ("identity", 1),
    ]
    assert game_indexes[0]["unique"] is True
    assert list(game_indexes[1]["key"].items())[-1] == ("game_date", 1)
    assert "unique" not in game_indexes[1]

    admin_index = admin_db.collections["admin"].indexes[0].document
    assert list(admin_index["key"].items()) == [("username", 1)]
    assert admin_index["unique"] is True
    assert admin_index["sparse"] is True
    assert "partialFilterExpression" not in admin_index

    history_index = admin_db.collections["execution_history"].indexes[0].document
    assert list(history_index["key"].items()) == [
        ("process", 1),
        ("queued_at", -1),
    ]
    assert "unique" not in history_index


@pytest.mark.asyncio
async def test_ensure_database_indexes_replaces_conflicting_definition():
    sports_db = FakeDatabase((*DATASET_COLLECTIONS, "games"))
    admin_db = FakeDatabase(("admin", "execution_history"))
    sports_db.collections["temp2"].existing_indexes = {
        DATASET_INDEX_NAME: {
            "key": [
                ("sport_type", 1),
                ("gender", 1),
                ("level", 1),
            ],
            "unique": True,
            "partialFilterExpression": {
                "sport_type": {"$type": "string"},
            },
        }
    }

    await ensure_database_indexes(sports_db, admin_db)

    assert sports_db.collections["temp2"].dropped_indexes == [
        DATASET_INDEX_NAME
    ]
