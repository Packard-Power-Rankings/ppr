from copy import deepcopy
from types import SimpleNamespace

import pytest

from api.service.admin_teams import AdminTeamsService


class FakeCollection:
    def __init__(self, document=None):
        self.document = deepcopy(document)
        self.updates = []

    async def find_one(self, _query, _projection=None):
        return self.document

    async def update_one(self, query, update):
        self.updates.append((query, update))
        if not self.document:
            return SimpleNamespace(matched_count=0, modified_count=0)

        for key, value in update.get("$set", {}).items():
            self.document[key] = value
        return SimpleNamespace(matched_count=1, modified_count=1)


class FakeGamesCollection:
    def __init__(self, documents):
        self.documents = deepcopy(documents)

    async def update_many(self, query, update):
        modified_count = 0
        for document in self.documents:
            if any(document.get(key) != value for key, value in query.items()):
                continue
            document.update(update.get("$set", {}))
            modified_count += 1
        return SimpleNamespace(modified_count=modified_count)


@pytest.mark.asyncio
async def test_update_team_name_updates_all_related_datastores():
    service = AdminTeamsService(("basketball", "mens", "high_school"))
    dataset_fields = {
        "_id": service.level_constant["_id"],
        "sport_type": "basketball",
        "gender": "mens",
        "level": "high_school",
    }
    teams = [
        {
            "team_id": 12,
            "team_name": "North Start Academy",
            "season_opp": [],
        },
        {
            "team_id": 20,
            "team_name": "Cedar Valley",
            "season_opp": [
                {
                    "game_id": "Cedar Valley_North Start Academy_2026-01-01",
                    "opponent_id": 12,
                    "opponent_name": "North Start Academy",
                }
            ],
        },
    ]
    service.sports_collection = FakeCollection({
        **dataset_fields,
        "teams": deepcopy(teams),
    })
    service.games_collection = FakeGamesCollection([
        {
            "sport_type": "basketball",
            "gender": "mens",
            "level": "high_school",
            "game_id": "12_20_2026-01-01",
            "home_team_id": 12,
            "home_team": "North Start Academy",
            "away_team_id": 20,
            "away_team": "Cedar Valley",
        },
        {
            "sport_type": "basketball",
            "gender": "mens",
            "level": "high_school",
            "game_id": "20_12_2026-01-02",
            "home_team_id": 20,
            "home_team": "Cedar Valley",
            "away_team_id": 12,
            "away_team": "North Start Academy",
        },
    ])
    service.flagged_games = FakeCollection({
        "_id": "flagged-document",
        **{key: value for key, value in dataset_fields.items() if key != "_id"},
        "flagged_games": [
            {
                "team1_id": 12,
                "team1_name": "Northstar Academy",
                "team2_id": 20,
                "team2_name": "Cedar Valley",
                "game_id": "Northstar Academy_Cedar Valley_2026-01-01",
            }
        ],
    })
    service.previous_season = FakeCollection({
        **dataset_fields,
        "teams": [
            {
                "team_id": 12,
                "team_name": "Northstar Academy",
                "season_opp": [],
            },
            {
                "team_id": 20,
                "team_name": "Cedar Valley",
                "season_opp": [
                    {
                        "game_id": "Cedar Valley_Northstar Academy_2025-01-01",
                        "opponent_id": 12,
                        "opponent_name": "Northstar Academy",
                    }
                ],
            },
        ],
    })

    response = await service.update_team_name(12, "  Northstar Prep  ")

    assert response["status"] == 200
    assert response["message"] == "North Start Academy was renamed to Northstar Prep"
    assert response["updated"] == {
        "team_records": 1,
        "game_records": 1,
        "game_ids": 1,
        "canonical_games": 2,
        "source_uploads_changed": 0,
        "flagged_games": 1,
        "flagged_game_ids": 1,
        "archived_team_records": 1,
        "archived_game_records": 1,
        "archived_game_ids": 1,
    }

    current_teams = service.sports_collection.document["teams"]
    assert current_teams[0]["team_name"] == "Northstar Prep"
    assert current_teams[1]["season_opp"][0]["opponent_name"] == "Northstar Prep"
    assert "Northstar Prep" in current_teams[1]["season_opp"][0]["game_id"]

    assert service.games_collection.documents[0]["home_team"] == "Northstar Prep"
    assert service.games_collection.documents[1]["away_team"] == "Northstar Prep"

    flagged_game = service.flagged_games.document["flagged_games"][0]
    assert flagged_game["team1_name"] == "Northstar Prep"
    assert "Northstar Prep" in flagged_game["game_id"]
    archived_teams = service.previous_season.document["teams"]
    assert archived_teams[0]["team_name"] == "Northstar Prep"
    assert archived_teams[1]["season_opp"][0]["opponent_name"] == "Northstar Prep"
    assert "Northstar Prep" in archived_teams[1]["season_opp"][0]["game_id"]


@pytest.mark.asyncio
async def test_update_team_info_updates_editable_metadata():
    service = AdminTeamsService(("basketball", "mens", "high_school"))
    service.sports_collection = FakeCollection({
        "_id": service.level_constant["_id"],
        "sport_type": "basketball",
        "gender": "mens",
        "level": "high_school",
        "teams": [{
            "team_id": 12,
            "team_name": "Northstar Academy",
            "short_name": "Northstar Academy",
            "long_name": "Northstar Academy",
            "state": "Oregon",
            "division": "5A",
            "conference": "West",
            "ranked": True,
        }],
    })

    response = await service.update_team_info(12, {
        "short_name": "Northstar Academy",
        "long_name": "Northstar Preparatory School",
        "state": "Washington",
        "division": "4A",
        "conference": "Northwest",
        "ranked": False,
    })

    assert response["status"] == 200
    assert service.sports_collection.document["teams"][0] == {
        "team_id": 12,
        "team_name": "Northstar Academy",
        "short_name": "Northstar Academy",
        "long_name": "Northstar Preparatory School",
        "state": "Washington",
        "division": "4A",
        "conference": "Northwest",
        "ranked": False,
    }
