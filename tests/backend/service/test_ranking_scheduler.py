from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from api.config.constants import LEVEL_CONSTANTS
from api.service import ranking_scheduler
from api.service import tasks


LEVEL_KEY = ("basketball", "mens", "high_school")


class FakeCursor:
    def __init__(self, documents):
        self.documents = deepcopy(documents)

    async def to_list(self, length=None):
        return self.documents if length is None else self.documents[:length]


class FakeCollection:
    def __init__(self, document=None, find_documents=None, update_many_count=0):
        self.document = deepcopy(document)
        self.find_documents = find_documents or []
        self.update_many_count = update_many_count
        self.updates = []
        self.update_many_calls = []
        self.find_query = None

    async def find_one(self, _query, _projection=None):
        return deepcopy(self.document)

    async def update_one(self, query, update):
        self.updates.append((deepcopy(query), deepcopy(update)))
        if not self.document:
            return SimpleNamespace(matched_count=0, modified_count=0)
        matches_revision = (
            "games_revision" not in query
            or query["games_revision"] == self.document.get("games_revision")
            or isinstance(query["games_revision"], dict)
        )
        matches_task = (
            "ranking_task_id" not in query
            or query["ranking_task_id"] == self.document.get("ranking_task_id")
        )
        if not matches_revision or not matches_task:
            return SimpleNamespace(matched_count=0, modified_count=0)
        self.document.update(update.get("$set", {}))
        if "$inc" in update:
            for field, amount in update["$inc"].items():
                self.document[field] = self.document.get(field, 0) + amount
        return SimpleNamespace(matched_count=1, modified_count=1)

    def find(self, query, _projection=None):
        self.find_query = deepcopy(query)
        return FakeCursor(self.find_documents)

    async def update_many(self, query, update):
        self.update_many_calls.append((deepcopy(query), deepcopy(update)))
        return SimpleNamespace(modified_count=self.update_many_count)


class FakeDatabase:
    def __init__(self, games, datasets):
        self.collections = {"games": games, "temp2": datasets}

    def get_collection(self, name):
        return self.collections[name]


class FakeRedis:
    def __init__(self, guard_acquired=True):
        self.guard_acquired = guard_acquired
        self.enqueued = []
        self.guards = []

    async def set(self, key, value, **options):
        self.guards.append((key, value, options))
        return self.guard_acquired

    async def enqueue_job(self, function, *args, **kwargs):
        self.enqueued.append((function, args, kwargs))
        return SimpleNamespace(job_id=kwargs.get("_job_id"))

    async def eval(self, *_args):
        return 1


def test_stale_update_increments_revision_and_records_latest_change():
    changed_at = datetime(2026, 10, 2, 15, 30, tzinfo=timezone.utc)

    update = ranking_scheduler.stale_ranking_update(
        now=changed_at,
        extra_fields={"teams": ["updated"]},
    )

    assert update["$inc"] == {"games_revision": 1}
    assert update["$set"] == {
        "rankings_stale": True,
        "ranking_status": "stale",
        "ranking_requested_at": changed_at,
        "ranking_error": None,
        "teams": ["updated"],
    }


@pytest.mark.asyncio
async def test_enqueue_uses_dataset_guard_and_full_algorithm(monkeypatch):
    dataset = {
        "_id": LEVEL_CONSTANTS[LEVEL_KEY]["_id"],
        "games_revision": 4,
        "rankings_stale": True,
    }
    games = FakeCollection(document={"_id": "game"})
    datasets = FakeCollection(document=dataset)
    monkeypatch.setattr(
        ranking_scheduler,
        "sports_database",
        FakeDatabase(games, datasets),
    )
    recorded = []

    async def record(*args, **kwargs):
        recorded.append((args, kwargs))

    monkeypatch.setattr(ranking_scheduler, "record_execution", record)
    redis = FakeRedis()

    result = await ranking_scheduler.enqueue_ranking_job(
        redis,
        LEVEL_KEY,
        iterations=3,
        trigger=ranking_scheduler.AUTOMATIC_TRIGGER,
    )

    assert result.queued is True
    assert redis.guards[0][0].endswith(":basketball:mens:high_school")
    assert redis.guards[0][2] == {"ex": 3600, "nx": True}
    assert redis.enqueued == [(
        "run_main_algorithm",
        (LEVEL_KEY, 3, "automatic"),
        {"_job_id": result.task_id},
    )]
    assert recorded[0][0][1:5] == (
        "algorithm",
        "basketball",
        "mens",
        "high_school",
    )
    assert recorded[0][1] == {"iterations": 3, "trigger": "automatic"}
    assert datasets.document["ranking_status"] == "queued"


@pytest.mark.asyncio
async def test_enqueue_suppresses_overlapping_dataset_job(monkeypatch):
    monkeypatch.setattr(
        ranking_scheduler,
        "sports_database",
        FakeDatabase(
            FakeCollection(document={"_id": "game"}),
            FakeCollection(document={"_id": LEVEL_CONSTANTS[LEVEL_KEY]["_id"]}),
        ),
    )
    redis = FakeRedis(guard_acquired=False)

    result = await ranking_scheduler.enqueue_ranking_job(redis, LEVEL_KEY)

    assert result == ranking_scheduler.RankingEnqueueResult(
        queued=False,
        reason="already_active",
    )
    assert redis.enqueued == []


@pytest.mark.asyncio
async def test_enqueue_marks_empty_dataset_without_creating_failed_job(monkeypatch):
    datasets = FakeCollection(document={
        "_id": LEVEL_CONSTANTS[LEVEL_KEY]["_id"],
        "games_revision": 8,
        "rankings_stale": True,
    })
    monkeypatch.setattr(
        ranking_scheduler,
        "sports_database",
        FakeDatabase(FakeCollection(), datasets),
    )
    redis = FakeRedis()

    result = await ranking_scheduler.enqueue_ranking_job(redis, LEVEL_KEY)

    assert result.reason == "no_games"
    assert datasets.document["rankings_stale"] is False
    assert datasets.document["ranked_revision"] == 8
    assert datasets.document["ranking_status"] == "no_games"
    assert redis.enqueued == []


@pytest.mark.asyncio
async def test_completed_run_remains_stale_when_revision_changed(monkeypatch):
    dataset = {
        "_id": LEVEL_CONSTANTS[LEVEL_KEY]["_id"],
        "games_revision": 5,
        "ranking_task_id": "task-id",
    }
    datasets = FakeCollection(document=dataset)
    monkeypatch.setattr(
        ranking_scheduler,
        "sports_database",
        FakeDatabase(FakeCollection(), datasets),
    )

    current = await ranking_scheduler.mark_ranking_complete(
        LEVEL_KEY,
        "task-id",
        started_revision=4,
    )

    assert current is False
    assert datasets.document["rankings_stale"] is True
    assert datasets.document["ranking_status"] == "stale"


@pytest.mark.asyncio
async def test_due_dispatch_uses_ten_minute_quiet_period(monkeypatch):
    datasets = FakeCollection(find_documents=[{
        "sport_type": "basketball",
        "gender": "mens",
        "level": "high_school",
    }])
    monkeypatch.setattr(
        ranking_scheduler,
        "sports_database",
        FakeDatabase(FakeCollection(), datasets),
    )
    monkeypatch.setenv("RANKING_DEBOUNCE_SECONDS", "600")
    queued = []

    async def enqueue(_redis, level_key, **kwargs):
        queued.append((level_key, kwargs))
        return ranking_scheduler.RankingEnqueueResult(
            queued=True,
            task_id="task-id",
        )

    monkeypatch.setattr(ranking_scheduler, "enqueue_ranking_job", enqueue)
    before = datetime.now(timezone.utc) - timedelta(seconds=601)

    result = await ranking_scheduler.dispatch_due_rankings({"redis": object()})

    cutoff = datasets.find_query["$or"][0]["ranking_requested_at"]["$lte"]
    after = datetime.now(timezone.utc) - timedelta(seconds=599)
    assert before <= cutoff <= after
    assert queued == [(LEVEL_KEY, {"trigger": "automatic"})]
    assert result["queued"] == 1


@pytest.mark.asyncio
async def test_weekly_snapshot_copies_current_rank_once_per_local_week(monkeypatch):
    datasets = FakeCollection(update_many_count=6)
    monkeypatch.setattr(
        ranking_scheduler,
        "sports_database",
        FakeDatabase(FakeCollection(), datasets),
    )
    captured_at = datetime(2026, 10, 4, 7, 0, tzinfo=timezone.utc)

    updated = await ranking_scheduler.snapshot_weekly_last_ranks(now=captured_at)

    assert updated == 6
    query, pipeline = datasets.update_many_calls[0]
    week_key = ranking_scheduler.weekly_snapshot_key(captured_at)
    assert query == {
        "teams.0": {"$exists": True},
        "last_rank_snapshot_week": {"$ne": week_key},
    }
    fields = pipeline[0]["$set"]
    assert fields["last_rank_snapshot_week"] == week_key
    assert fields["last_rank_snapshot_at"] == captured_at
    rank_expression = fields["teams"]["$map"]["in"]["$mergeObjects"][1]
    assert rank_expression == {
        "last_rank": {"$ifNull": ["$$team.overall_rank", 0]}
    }


@pytest.mark.asyncio
async def test_weekly_scheduler_snapshots_before_dispatching_stale_jobs(monkeypatch):
    calls = []

    async def snapshot():
        calls.append("snapshot")
        return 6

    async def dispatch(redis, *, trigger, quiet_before):
        calls.append(("dispatch", redis, trigger, quiet_before))
        return {
            "queued": 2,
            "already_active": 0,
            "no_games": 0,
            "failed": 0,
        }

    monkeypatch.setattr(ranking_scheduler, "snapshot_weekly_last_ranks", snapshot)
    monkeypatch.setattr(ranking_scheduler, "_dispatch_stale_rankings", dispatch)
    redis = object()

    result = await ranking_scheduler.weekly_ranking_catchup({"redis": redis})

    assert calls == [
        "snapshot",
        ("dispatch", redis, ranking_scheduler.WEEKLY_TRIGGER, None),
    ]
    assert result == {
        "queued": 2,
        "already_active": 0,
        "no_games": 0,
        "failed": 0,
        "last_rank_snapshots": 6,
    }


def test_worker_cron_runs_weekly_sunday_at_one_am():
    weekly = next(
        job for job in tasks.WorkerSettings.cron_jobs
        if job.name == "weekly_ranking_catchup"
    )

    assert weekly.weekday == "sun"
    assert weekly.hour == 1
    assert weekly.minute == 0
    assert str(tasks.WorkerSettings.timezone) == "America/Denver"
