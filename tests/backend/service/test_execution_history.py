from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from api.routers import admin_routes
from api.schemas.items import InputMethod
from api.service import execution_history
from api.service import tasks


class FakeCursor:
    def __init__(self, documents):
        self.documents = documents

    def sort(self, field, direction):
        self.documents.sort(
            key=lambda document: document[field], reverse=direction < 0)
        return self

    def limit(self, count):
        self.documents = self.documents[:count]
        return self

    def skip(self, count):
        self.documents = self.documents[count:]
        return self

    async def to_list(self, length=None):
        documents = self.documents if length is None else self.documents[:length]
        self.documents = self.documents[len(documents):]
        return documents


class FakeCollection:
    def __init__(self):
        self.documents = []

    async def insert_one(self, document):
        self.documents.append(deepcopy(document))

    async def update_one(self, query, update):
        document = next(
            item for item in self.documents if item["_id"] == query["_id"]
        )
        document.update(update["$set"])

    async def delete_many(self, query):
        obsolete_ids = set(query["_id"]["$in"])
        before_count = len(self.documents)
        self.documents = [
            document for document in self.documents
            if document["_id"] not in obsolete_ids
        ]
        return SimpleNamespace(deleted_count=before_count - len(self.documents))

    def find(self, query, projection):
        documents = [
            {key: value for key, value in item.items() if projection.get(key, 1)}
            for item in self.documents
            if item["process"] == query["process"]
        ]
        return FakeCursor(documents)


class FakeDatabase:
    def __init__(self):
        self.collection = FakeCollection()

    def get_collection(self, _name):
        return self.collection


@pytest.mark.asyncio
async def test_execution_records_track_status_and_return_five_recent_per_process(monkeypatch):
    database = FakeDatabase()
    monkeypatch.setattr(execution_history, "admin_database", database)
    for index in range(14):
        process = (
            execution_history.ALGORITHM_PROCESS
            if index % 2 == 0
            else execution_history.Z_SCORE_PROCESS
        )
        await execution_history.record_execution(
            task_id=f"task-{index}",
            process=process,
            sport_type="football",
            gender="mens",
            level="high_school",
            iterations=3 if process == execution_history.ALGORITHM_PROCESS else None,
        )
        assert sum(
            item["process"] == process
            for item in database.collection.documents
        ) <= execution_history.HISTORY_LIMIT

    await execution_history.update_execution_status("task-12", "in_progress")
    await execution_history.update_execution_status("task-12", "complete")
    history = await execution_history.recent_execution_history()

    assert [item["task_id"] for item in history[execution_history.ALGORITHM_PROCESS]] == [
        "task-12", "task-10", "task-8", "task-6", "task-4",
    ]
    assert [item["task_id"] for item in history[execution_history.Z_SCORE_PROCESS]] == [
        "task-13", "task-11", "task-9", "task-7", "task-5",
    ]
    completed = history[execution_history.ALGORITHM_PROCESS][0]
    assert completed["status"] == "complete"
    assert completed["trigger"] == "manual"
    assert completed["started_at"] is not None
    assert completed["finished_at"] is not None
    assert completed["finished_at"].endswith("Z")


@pytest.mark.asyncio
async def test_execution_status_accepts_worker_result_timestamps(monkeypatch):
    database = FakeDatabase()
    monkeypatch.setattr(execution_history, "admin_database", database)
    await execution_history.record_execution(
        task_id="worker-result",
        process=execution_history.ALGORITHM_PROCESS,
        sport_type="football",
        gender="mens",
        level="college",
    )
    started_at = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
    finished_at = datetime(2026, 10, 1, 12, 5, tzinfo=timezone.utc)

    await execution_history.update_execution_status(
        "worker-result",
        "complete",
        started_at=started_at,
        finished_at=finished_at,
    )

    record = database.collection.documents[0]
    assert record["status"] == "complete"
    assert record["started_at"] == "2026-10-01T12:00:00Z"
    assert record["finished_at"] == "2026-10-01T12:05:00Z"


@pytest.mark.asyncio
async def test_prune_removes_excess_existing_records_per_process(monkeypatch):
    database = FakeDatabase()
    monkeypatch.setattr(execution_history, "admin_database", database)
    start_time = datetime(2026, 10, 1, tzinfo=timezone.utc)

    for process in (
        execution_history.ALGORITHM_PROCESS,
        execution_history.Z_SCORE_PROCESS,
    ):
        for index in range(8):
            database.collection.documents.append({
                "_id": f"{process}-{index}",
                "task_id": f"{process}-{index}",
                "process": process,
                "queued_at": (
                    start_time + timedelta(seconds=index)
                ).isoformat().replace("+00:00", "Z"),
            })

    await execution_history.prune_execution_history()

    for process in (
        execution_history.ALGORITHM_PROCESS,
        execution_history.Z_SCORE_PROCESS,
    ):
        remaining = [
            record for record in database.collection.documents
            if record["process"] == process
        ]
        assert len(remaining) == execution_history.HISTORY_LIMIT
        assert {record["task_id"] for record in remaining} == {
            f"{process}-{index}" for index in range(3, 8)
        }


@pytest.mark.asyncio
async def test_history_keeps_five_recent_records_per_dataset_and_process(monkeypatch):
    database = FakeDatabase()
    monkeypatch.setattr(execution_history, "admin_database", database)
    start_time = datetime(2026, 10, 1, tzinfo=timezone.utc)

    for process in (
        execution_history.ALGORITHM_PROCESS,
        execution_history.Z_SCORE_PROCESS,
    ):
        for sport_type, gender, level in (
            ("football", "mens", "high_school"),
            ("basketball", "womens", "college"),
        ):
            for index in range(7):
                task_id = f"{process}-{sport_type}-{index}"
                database.collection.documents.append({
                    "_id": task_id,
                    "task_id": task_id,
                    "process": process,
                    "sport_type": sport_type,
                    "gender": gender,
                    "level": level,
                    "queued_at": (
                        start_time + timedelta(seconds=index)
                    ).isoformat().replace("+00:00", "Z"),
                })

    history = await execution_history.recent_execution_history()

    for process in (
        execution_history.ALGORITHM_PROCESS,
        execution_history.Z_SCORE_PROCESS,
    ):
        assert len(history[process]) == 10
        for sport_type in ("football", "basketball"):
            retained_ids = {
                record["task_id"] for record in history[process]
                if record["sport_type"] == sport_type
            }
            assert retained_ids == {
                f"{process}-{sport_type}-{index}" for index in range(2, 7)
            }


@pytest.mark.asyncio
async def test_worker_records_successful_algorithm_and_z_score_runs(monkeypatch):
    status_updates = []
    ranking_updates = []

    class FakeAdminTeamsService:
        def __init__(self, _level_key):
            pass

        async def run_main_algorithm(self, _iterations):
            pass

        async def calculate_z_scores(self):
            pass

    async def record_status(task_id, status, **_details):
        status_updates.append((task_id, status))

    async def mark_started(level_key, task_id, trigger):
        ranking_updates.append(("started", level_key, task_id, trigger))
        return 7

    async def mark_complete(level_key, task_id, revision):
        ranking_updates.append(("complete", level_key, task_id, revision))
        return True

    monkeypatch.setattr(tasks, "AdminTeamsService", FakeAdminTeamsService)
    monkeypatch.setattr(tasks, "update_execution_status", record_status)
    monkeypatch.setattr(tasks, "mark_ranking_started", mark_started)
    monkeypatch.setattr(tasks, "mark_ranking_complete", mark_complete)

    await tasks.run_main_algorithm(
        {"job_id": "algo-id"},
        ("football", "mens", "college"),
        4,
    )
    await tasks.calc_z_score(
        {"job_id": "z-id"},
        ("basketball", "womens", "high_school"),
    )

    assert status_updates == [
        ("algo-id", "in_progress"),
        ("algo-id", "complete"),
        ("z-id", "in_progress"),
        ("z-id", "complete"),
    ]
    assert ranking_updates == [
        (
            "started",
            ("football", "mens", "college"),
            "algo-id",
            "manual",
        ),
        ("complete", ("football", "mens", "college"), "algo-id", 7),
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("process", [
    execution_history.ALGORITHM_PROCESS,
    execution_history.Z_SCORE_PROCESS,
])
async def test_worker_records_failed_runs(monkeypatch, process):
    status_updates = []
    ranking_failures = []

    class FakeAdminTeamsService:
        def __init__(self, _level_key):
            pass

        async def run_main_algorithm(self, _iterations):
            raise RuntimeError("algorithm failed")

        async def calculate_z_scores(self):
            raise RuntimeError("z-score calculation failed")

    async def record_status(task_id, status, **details):
        status_updates.append((task_id, status, details))

    async def mark_started(_level_key, _task_id, _trigger):
        return 7

    async def mark_failed(level_key, task_id, error):
        ranking_failures.append((level_key, task_id, error))

    monkeypatch.setattr(tasks, "AdminTeamsService", FakeAdminTeamsService)
    monkeypatch.setattr(tasks, "update_execution_status", record_status)
    monkeypatch.setattr(tasks, "mark_ranking_started", mark_started)
    monkeypatch.setattr(tasks, "mark_ranking_failed", mark_failed)

    with pytest.raises(RuntimeError):
        if process == execution_history.ALGORITHM_PROCESS:
            await tasks.run_main_algorithm(
                {"job_id": "failed-task"},
                ("football", "mens", "college"),
                3,
            )
        else:
            await tasks.calc_z_score(
                {"job_id": "failed-task"},
                ("football", "mens", "college"),
            )

    assert status_updates[0] == ("failed-task", "in_progress", {})
    task_id, status, details = status_updates[1]
    assert (task_id, status) == ("failed-task", "failed")
    assert details["error"]["type"] == "RuntimeError"
    assert process.split("_")[0] in details["error"]["message"]
    assert "test_execution_history.py" in details["error"]["location"]
    if process == execution_history.ALGORITHM_PROCESS:
        assert ranking_failures[0][0:2] == (
            ("football", "mens", "college"),
            "failed-task",
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("process", "iterations"),
    [
        (execution_history.ALGORITHM_PROCESS, 3),
        (execution_history.Z_SCORE_PROCESS, None),
    ],
)
async def test_enqueue_records_and_forwards_the_same_task_id(
    monkeypatch,
    process,
    iterations,
):
    recorded = []

    class FakeRedis:
        async def enqueue_job(self, function, *args, **kwargs):
            self.job = SimpleNamespace(
                function=function, args=args, kwargs=kwargs)
            return self.job

    redis = FakeRedis()

    async def fake_record_execution(*args, **kwargs):
        recorded.append((args, kwargs))

    monkeypatch.setattr(admin_routes, "record_execution",
                        fake_record_execution)
    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(redis=redis)),
    )
    sport_input = InputMethod(
        sport_type="football",
        gender="mens",
        level="college",
    )

    if process == execution_history.ALGORITHM_PROCESS:
        async def fake_enqueue(_redis, level_key, **kwargs):
            recorded.append((("algorithm-task", *level_key), kwargs))
            return SimpleNamespace(
                queued=True,
                task_id="algorithm-task",
                reason=None,
            )

        monkeypatch.setattr(
            admin_routes,
            "enqueue_ranking_job",
            fake_enqueue,
        )
        response = await admin_routes.main_algorithm_exc(3, request, sport_input)
        assert recorded[0] == (
            ("algorithm-task", "football", "mens", "college"),
            {"iterations": 3, "trigger": "manual"},
        )
    else:
        response = await admin_routes.calc_z_scores(request, sport_input)
        assert redis.job.function == "calc_z_score"
        assert redis.job.args == (("football", "mens", "college"),)

    task_id = response["task_id"]
    if process == execution_history.Z_SCORE_PROCESS:
        assert recorded[0][0][:5] == (
            task_id,
            process,
            "football",
            "mens",
            "college",
        )
        assert recorded[0][1] == {}
        assert redis.job.kwargs["_job_id"] == task_id
        assert "task_id" not in redis.job.kwargs


@pytest.mark.asyncio
async def test_history_repairs_completed_and_orphaned_worker_jobs(monkeypatch):
    started_at = datetime(2026, 10, 1, 13, 0, tzinfo=timezone.utc)
    finished_at = datetime(2026, 10, 1, 13, 2, tzinfo=timezone.utc)
    history = {
        execution_history.ALGORITHM_PROCESS: [{
            "task_id": "completed-job",
            "status": "queued",
        }],
        execution_history.Z_SCORE_PROCESS: [{
            "task_id": "orphaned-job",
            "status": "failed",
            "error": None,
        }, {
            "task_id": "failed-job-with-result",
            "status": "failed",
            "error": None,
        }, {
            "task_id": "unreadable-job",
            "status": "failed",
            "error": None,
        }],
    }

    class FakeJob:
        def __init__(self, job_id, redis):
            self.job_id = job_id

        async def status(self):
            if self.job_id in {
                "completed-job",
                "failed-job-with-result",
                "unreadable-job",
            }:
                return admin_routes.JobStatus.complete
            return admin_routes.JobStatus.not_found

        async def result_info(self):
            if self.job_id == "unreadable-job":
                raise ValueError("cannot deserialize result")
            if self.job_id == "failed-job-with-result":
                return SimpleNamespace(
                    success=False,
                    result=RuntimeError("No games were found"),
                    start_time=started_at,
                    finish_time=finished_at,
                )
            return SimpleNamespace(
                success=True,
                result=None,
                start_time=started_at,
                finish_time=finished_at,
            )

    async def recent_history():
        return deepcopy(history)

    async def update_status(task_id, status, **timestamps):
        for records in history.values():
            for record in records:
                if record["task_id"] == task_id:
                    record["status"] = status
                    record.update(timestamps)

    monkeypatch.setattr(admin_routes, "Job", FakeJob)
    monkeypatch.setattr(
        admin_routes, "recent_execution_history", recent_history)
    monkeypatch.setattr(admin_routes, "update_execution_status", update_status)
    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(redis=object())),
    )

    response = await admin_routes.get_execution_history(request)

    completed = response[execution_history.ALGORITHM_PROCESS][0]
    orphaned = response[execution_history.Z_SCORE_PROCESS][0]
    assert completed == {
        "task_id": "completed-job",
        "status": "complete",
        "started_at": started_at,
        "finished_at": finished_at,
        "error": None,
    }
    assert orphaned["status"] == "failed"
    assert orphaned["error"]["type"] == "WorkerResultUnavailable"
    recovered = response[execution_history.Z_SCORE_PROCESS][1]
    assert recovered["error"] == {
        "type": "RuntimeError",
        "message": "No games were found",
        "location": "Background worker",
    }
    unreadable = response[execution_history.Z_SCORE_PROCESS][2]
    assert unreadable["error"]["type"] == "WorkerResultUnreadable"
    assert "ValueError" in unreadable["error"]["message"]
