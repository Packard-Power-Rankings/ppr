from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from api.service.admin_teams import AdminTeamsService


class FakeGamesCollection:
    def __init__(self, game):
        self.game = game
        self.query = None

    async def find_one(self, query):
        self.query = query
        return self.game


class FakeFlaggedCollection:
    def __init__(self, modified_count=1):
        self.calls = []
        self.modified_count = modified_count

    async def update_one(self, query, update, upsert=False):
        self.calls.append((query, update, upsert))
        modified_count = 0 if "$setOnInsert" in update else self.modified_count
        return SimpleNamespace(modified_count=modified_count)


@pytest.mark.asyncio
async def test_flagged_game_must_exist_and_stores_canonical_team_data():
    service = AdminTeamsService(("basketball", "mens", "high_school"))
    service.games_collection = FakeGamesCollection({
        "game_id": "12_34_2026-01-01",
        "home_team_id": 12,
        "home_team": "Canonical Home",
        "away_team_id": 34,
        "away_team": "Canonical Away",
    })
    service.flagged_games = FakeFlaggedCollection()

    result = await service.store_flagged_games(
        "12_34_2026-01-01",
        34,
        12,
        "The home score should be 74, not 72.",
    )

    assert result == {
        "message": "Game was successfully reported",
        "game_flagged": 1,
        "status": 200,
    }
    lookup = service.games_collection.query
    assert lookup["game_id"] == "12_34_2026-01-01"
    add_update = service.flagged_games.calls[1][1]
    flagged_game = add_update["$push"]["flagged_games"]
    assert flagged_game == {
        "issue_id": flagged_game["issue_id"],
        "game_id": "12_34_2026-01-01",
        "team1_id": 12,
        "team1_name": "Canonical Home",
        "team2_id": 34,
        "team2_name": "Canonical Away",
        "description": "The home score should be 74, not 72.",
        "reported_at": flagged_game["reported_at"],
        "status": "open",
    }
    assert len(flagged_game["issue_id"]) == 32
    assert isinstance(flagged_game["reported_at"], datetime)


@pytest.mark.asyncio
async def test_flagged_game_rejects_unknown_game():
    service = AdminTeamsService(("basketball", "mens", "high_school"))
    service.games_collection = FakeGamesCollection(None)

    with pytest.raises(HTTPException) as error:
        await service.store_flagged_games(
            "unknown-game",
            12,
            34,
            "This game has the wrong score.",
        )

    assert error.value.status_code == 404
