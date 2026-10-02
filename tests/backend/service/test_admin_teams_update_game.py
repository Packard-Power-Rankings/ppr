from copy import deepcopy
from types import SimpleNamespace

import pytest

from api.service.admin_teams import AdminTeamsService


class FakeCollection:
    def __init__(self, document=None):
        self.document = deepcopy(document)

    async def find_one(self, _query, _projection=None):
        return self.document

    async def update_one(self, _query, update):
        if not self.document:
            return SimpleNamespace(matched_count=0, modified_count=0)
        for key, value in update.get("$set", {}).items():
            self.document[key] = value
        return SimpleNamespace(matched_count=1, modified_count=1)


class FakeCursor:
    def __init__(self, documents):
        self.documents = deepcopy(documents)
        self.sort_fields = None

    def sort(self, fields):
        self.sort_fields = fields
        return self

    async def to_list(self, length=None):
        return self.documents


class FakeGamesCollection:
    def __init__(self, documents):
        self.documents = documents
        self.query = None
        self.projection = None
        self.cursor = None

    def find(self, query, projection=None):
        self.query = deepcopy(query)
        self.projection = deepcopy(projection)
        self.cursor = FakeCursor(self.documents)
        return self.cursor


@pytest.mark.asyncio
async def test_update_game_updates_canonical_and_materialized_records():
    service = AdminTeamsService(("basketball", "mens", "high_school"))
    game_id = "1_2_2026-01-09"
    dataset_fields = {
        "_id": service.level_constant["_id"],
        "sport_type": "basketball",
        "gender": "mens",
        "level": "high_school",
    }
    teams = [
        {
            "team_id": 1,
            "team_name": "Northstar Academy",
            "wins": 1,
            "losses": 0,
            "season_opp": [
                {
                    "game_id": game_id,
                    "game_date": "2026-01-09",
                    "opponent_id": 2,
                    "opponent_name": "Cedar Valley",
                    "home_team": 1,
                    "home_score": 72,
                    "away_score": 61,
                }
            ],
        },
        {
            "team_id": 2,
            "team_name": "Cedar Valley",
            "wins": 0,
            "losses": 1,
            "season_opp": [
                {
                    "game_id": game_id,
                    "game_date": "2026-01-09",
                    "opponent_id": 1,
                    "opponent_name": "Northstar Academy",
                    "home_team": 0,
                    "home_score": 72,
                    "away_score": 61,
                }
            ],
        },
    ]
    service.sports_collection = FakeCollection({
        **dataset_fields,
        "teams": teams,
    })
    service.games_collection = FakeCollection({
        "_id": "canonical-game",
        "sport_type": "basketball",
        "gender": "mens",
        "level": "high_school",
        "game_id": game_id,
        "game_date": "2026-01-09",
        "home_team_id": 1,
        "away_team_id": 2,
        "home_score": 72,
        "away_score": 61,
    })

    response = await service.update_teams_info(
        "Northstar Academy",
        60,
        "Cedar Valley",
        70,
        "2026-01-09",
        game_id
    )

    assert response["status"] == 200
    updated_teams = service.sports_collection.document["teams"]
    assert updated_teams[0]["wins"] == 0
    assert updated_teams[0]["losses"] == 1
    assert updated_teams[1]["wins"] == 1
    assert updated_teams[1]["losses"] == 0
    assert updated_teams[0]["season_opp"][0]["home_score"] == 60
    assert updated_teams[1]["season_opp"][0]["away_score"] == 70

    assert service.games_collection.document["home_score"] == 60
    assert service.games_collection.document["away_score"] == 70
    assert response["updated"] == {
        "game_id": game_id,
        "canonical_games": 1,
        "team_game_records": 2,
        "source_upload_changed": False,
    }


@pytest.mark.asyncio
async def test_find_season_dates_returns_orientation_and_scores():
    service = AdminTeamsService(("basketball", "mens", "high_school"))
    service.games_collection = FakeGamesCollection([
        {
            "game_id": "1_2_2026-01-09",
            "game_date": "2026-01-09",
            "home_team_id": 1,
            "home_team": "Northstar Academy",
            "away_team_id": 2,
            "away_team": "Cedar Valley",
            "home_score": 72,
            "away_score": 61,
        }
    ])

    games = await service.find_season_opp_dates(2, 1)

    assert games == [
        {
            "game_date": "2026-01-09",
            "game_id": "1_2_2026-01-09",
            "home_team_id": 1,
            "home_team_name": "Northstar Academy",
            "away_team_id": 2,
            "away_team_name": "Cedar Valley",
            "home_score": 72,
            "away_score": 61,
        }
    ]
    assert service.games_collection.query == {
        "sport_type": "basketball",
        "gender": "mens",
        "level": "high_school",
        "$or": [
            {"home_team_id": 2, "away_team_id": 1},
            {"home_team_id": 1, "away_team_id": 2},
        ],
    }
    assert service.games_collection.cursor.sort_fields == [
        ("game_date", 1),
        ("game_id", 1),
    ]


@pytest.mark.asyncio
async def test_find_season_dates_ignores_retained_team_history():
    service = AdminTeamsService(("basketball", "mens", "high_school"))
    service.sports_collection = FakeCollection({
        "teams": [{
            "team_id": 1,
            "season_opp": [{
                "game_id": "1_2_2025-12-20",
                "game_date": "2025-12-20",
                "opponent_id": 2,
            }],
        }],
    })
    service.games_collection = FakeGamesCollection([])

    games = await service.find_season_opp_dates(1, 2)

    assert games == []
