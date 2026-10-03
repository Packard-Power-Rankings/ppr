from copy import deepcopy
from types import SimpleNamespace

import pytest

from api.service.admin_teams import AdminTeamsService


class FakeCursor:
    def __init__(self, documents=None):
        self.documents = documents or []

    async def to_list(self, length=None):
        return self.documents


class FakeRelatedCollection:
    def __init__(self, deleted_count=0):
        self.deleted_count = deleted_count
        self.queries = []

    def find(self, query, _projection=None):
        self.queries.append(query)
        return FakeCursor()

    async def delete_many(self, query):
        self.queries.append(query)
        return SimpleNamespace(deleted_count=self.deleted_count)


class FakeCollection:
    name = "temp2"

    def __init__(self, document_count=6):
        self.document_count = document_count
        self.pipelines = []

    def aggregate(self, pipeline):
        self.pipelines.append(deepcopy(pipeline))
        return FakeCursor()

    async def count_documents(self, _query):
        return self.document_count

    async def find_one(self, _query):
        return {"teams": []} if self.document_count else None


@pytest.mark.asyncio
async def test_reset_all_sports_does_not_copy_data_to_previous_season():
    service = AdminTeamsService(("football", "mens", "high_school"))
    service.sports_collection = FakeCollection()
    service.csv_collection = FakeRelatedCollection(6)
    service.games_collection = FakeRelatedCollection(60)

    response = await service.reset_all_sports()

    assert len(service.sports_collection.pipelines) == 1
    reset_pipeline = service.sports_collection.pipelines[0]
    assert not any("$out" in stage for stage in reset_pipeline)
    assert not any("$match" in stage for stage in reset_pipeline)
    assert reset_pipeline[-1]["$merge"]["into"] == "temp2"
    reset_document = reset_pipeline[0]["$addFields"]
    assert reset_document["rankings_stale"] is False
    assert reset_document["ranking_status"] == "no_games"
    assert reset_document["games_revision"] == {
        "$add": [{"$ifNull": ["$games_revision", 0]}, 1]
    }
    reset_values = reset_pipeline[0]["$addFields"]["teams"]["$map"]["in"][
        "$mergeObjects"
    ][1]
    assert reset_values == {
        "win_ratio": 0.0,
        "wins": 0,
        "losses": 0,
        "season_initial_power": {
            "$cond": [
                {"$isArray": "$$team.power_ranking"},
                {"$cond": [
                    {"$gt": [{"$size": "$$team.power_ranking"}, 0]},
                    {"$arrayElemAt": ["$$team.power_ranking", -1]},
                    None,
                ]},
                None,
            ]
        },
        "season_opp": {
            "$cond": [
                {"$isArray": "$$team.season_opp"},
                {"$slice": ["$$team.season_opp", -5]},
                [],
            ]
        },
    }
    assert not {
        "overall_rank",
        "division_rank",
        "power_ranking",
        "date",
        "recent_opp",
    }.intersection(reset_values)
    assert response == {
        "archive_unchanged": True,
        "datasets_reset": 6,
        "games_deleted": 60,
        "upload_files_deleted": 0,
        "upload_records_deleted": 6,
        "return_data": "Reset 6 sports datasets",
    }


@pytest.mark.asyncio
async def test_selected_season_reset_remains_scoped_to_its_dataset():
    service = AdminTeamsService(("basketball", "womens", "college"))
    service.sports_collection = FakeCollection()
    service.csv_collection = FakeRelatedCollection(1)
    service.games_collection = FakeRelatedCollection(10)

    response = await service.clear_season()

    reset_pipeline = service.sports_collection.pipelines[0]
    assert not any("$out" in stage for stage in reset_pipeline)
    assert reset_pipeline[0] == {
        "$match": {"_id": service.level_constant["_id"]}
    }
    reset_values = reset_pipeline[1]["$addFields"]["teams"]["$map"]["in"][
        "$mergeObjects"
    ][1]
    assert reset_values["season_opp"] == {
        "$cond": [
            {"$isArray": "$$team.season_opp"},
            {"$slice": ["$$team.season_opp", -5]},
            [],
        ]
    }
    assert reset_pipeline[1]["$addFields"]["rankings_stale"] is False
    assert reset_pipeline[1]["$addFields"]["ranking_status"] == "no_games"
    assert response["archive_unchanged"] is True
    assert response["teams_reset"] is True
    assert response["games_deleted"] == 10
    assert service.games_collection.queries[0] == {
        "sport_type": "basketball",
        "gender": "womens",
        "level": "college",
    }
