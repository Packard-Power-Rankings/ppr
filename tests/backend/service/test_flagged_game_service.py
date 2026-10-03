from datetime import datetime, timezone
from types import SimpleNamespace

from bson import ObjectId
from fastapi import HTTPException
import pytest

from api.service import flagged_game_service


class FakeCursor:
    def __init__(self, documents):
        self.documents = documents

    async def to_list(self, length=None):
        return self.documents if length is None else self.documents[:length]


class FakeCollection:
    def __init__(self, documents=None, aggregate_results=None, modified_count=1):
        self.documents = documents or []
        self.aggregate_results = list(aggregate_results or [])
        self.modified_count = modified_count
        self.updates = []
        self.pipelines = []

    def find(self, _query, _projection=None):
        return FakeCursor(self.documents)

    def aggregate(self, pipeline):
        self.pipelines.append(pipeline)
        return FakeCursor(self.aggregate_results.pop(0))

    async def update_one(self, query, update):
        self.updates.append((query, update))
        return SimpleNamespace(
            matched_count=self.modified_count,
            modified_count=self.modified_count,
        )


class FakeDatabase:
    def __init__(self, collection):
        self.collection = collection

    def get_collection(self, _name):
        return self.collection


@pytest.mark.asyncio
async def test_migration_backfills_legacy_issue_metadata(monkeypatch):
    document_id = ObjectId()
    collection = FakeCollection(documents=[{
        "_id": document_id,
        "flagged_games": [{
            "game_id": "1_2_2026-01-01",
            "team1_id": 1,
            "team1_name": "Home",
            "team2_id": 2,
            "team2_name": "Away",
        }],
    }])
    monkeypatch.setattr(
        flagged_game_service,
        "sports_database",
        FakeDatabase(collection),
    )

    await flagged_game_service.migrate_legacy_flagged_games()

    issue = collection.updates[0][1]["$set"]["flagged_games"][0]
    assert len(issue["issue_id"]) == 32
    assert issue["description"] == flagged_game_service.LEGACY_ISSUE_DESCRIPTION
    assert issue["status"] == "open"
    assert isinstance(issue["reported_at"], datetime)


@pytest.mark.asyncio
async def test_list_returns_oldest_open_issues_and_total(monkeypatch):
    issues = [{
        "issue_id": "oldest",
        "description": "Incorrect home score",
    }]
    collection = FakeCollection(aggregate_results=[issues, [{"count": 3}]])
    service = flagged_game_service.FlaggedGameService()
    service.collection = collection

    result = await service.list_open_issues(skip=0, limit=50)

    assert result == {
        "issues": issues,
        "count": 3,
        "skip": 0,
        "limit": 50,
    }
    list_pipeline = collection.pipelines[0]
    assert list_pipeline[1] == {
        "$match": {"flagged_games.status": {"$ne": "resolved"}}
    }
    assert {"$sort": {"reported_at": 1, "issue_id": 1}} in list_pipeline


@pytest.mark.asyncio
async def test_list_marks_naive_mongo_report_timestamps_as_utc():
    reported_at = datetime(2026, 10, 3, 3, 54)
    collection = FakeCollection(aggregate_results=[
        [{"issue_id": "issue-123", "reported_at": reported_at}],
        [{"count": 1}],
    ])
    service = flagged_game_service.FlaggedGameService()
    service.collection = collection

    result = await service.list_open_issues(skip=0, limit=50)

    assert result["issues"][0]["reported_at"] == reported_at.replace(
        tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_resolve_marks_only_selected_open_issue():
    collection = FakeCollection(modified_count=1)
    service = flagged_game_service.FlaggedGameService()
    service.collection = collection

    result = await service.resolve_issue("issue-123")

    query, update = collection.updates[0]
    assert query == {
        "flagged_games": {
            "$elemMatch": {
                "issue_id": "issue-123",
                "status": {"$ne": "resolved"},
            }
        }
    }
    assert update["$set"]["flagged_games.$.status"] == "resolved"
    assert result["issue_id"] == "issue-123"


@pytest.mark.asyncio
async def test_resolve_rejects_missing_or_resolved_issue():
    collection = FakeCollection(modified_count=0)
    service = flagged_game_service.FlaggedGameService()
    service.collection = collection

    with pytest.raises(HTTPException) as error:
        await service.resolve_issue("missing")

    assert error.value.status_code == 404
