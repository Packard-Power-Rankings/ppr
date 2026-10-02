import asyncio
from types import SimpleNamespace

import pytest
from unittest.mock import AsyncMock

from fastapi import HTTPException

from api.service.admin_teams import AdminTeamsService
from api.service.game_ingestion import (
    canonical_game_identity,
    GameFileValidationError,
    game_identity,
    parse_game_csv,
    serialize_game_rows,
)


class FakeCursor:
    def __init__(self, documents):
        self.documents = documents

    async def to_list(self, length=None):
        return self.documents


class FakeGamesCollection:
    def __init__(self, existing=None):
        self.existing = existing or []
        self.inserted = []

    def find(self, _query, _projection=None):
        return FakeCursor(self.existing)

    async def insert_many(self, documents, ordered=True):
        self.inserted.extend(documents)
        return SimpleNamespace(inserted_ids=list(range(len(documents))))

    async def delete_many(self, _query):
        return SimpleNamespace(deleted_count=0)


def test_parse_game_csv_validates_and_normalizes_rows():
    games = parse_game_csv(
        b"2026-01-15,  Central   High ,Lincoln High,72,68,0\n"
        b"01/16/2026,Lincoln High,West Prep,65,70,999\n"
    )

    assert len(games) == 2
    assert games[0].home_team == "Central High"
    assert games[0].home_score == 72
    assert games[1].neutral_site == 999
    assert serialize_game_rows(games).decode("utf-8").splitlines()[0] == (
        "2026-01-15,Central High,Lincoln High,72,68,0"
    )


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (b"", "does not contain any games"),
        (
            b"date,home_team,away_team,home_score,away_score,neutral_site\n",
            "headerless",
        ),
        (b"2026-01-15,Team A,Team B,72,68\n", "expected 6 columns"),
        (b"not-a-date,Team A,Team B,72,68,0\n", "date must use"),
        (b"2026-01-15,Team A,Team A,72,68,0\n", "must be different"),
        (b"2026-01-15,Team A,Team B,nope,68,0\n", "nonnegative integer"),
        (b"2026-01-15,Team A,Team B,72,68,1\n", "must be 0 or 999"),
    ],
)
def test_parse_game_csv_rejects_invalid_game_files(content, message):
    with pytest.raises(GameFileValidationError, match=message):
        parse_game_csv(content)


def test_parse_game_csv_rejects_reversed_duplicate_game():
    content = (
        b"2026-01-15,Team A,Team B,72,68,0\n"
        b"01/15/2026,team b,team a,68,72,0\n"
    )

    with pytest.raises(GameFileValidationError, match="duplicates row 1"):
        parse_game_csv(content)


def test_game_identity_is_case_and_home_away_independent():
    assert game_identity("2026-01-15", "Team A", "Team B") == game_identity(
        "01/15/2026",
        " team b ",
        "team a",
    )


@pytest.mark.asyncio
async def test_ingestion_creates_missing_teams_and_stores_validated_games(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))
    service = AdminTeamsService(("basketball", "mens", "high_school"))
    service._ingest_lock = asyncio.Lock()
    service.find_missing_teams = AsyncMock(
        return_value=["Central High", "Lincoln High"]
    )
    service.add_teams_to_db = AsyncMock(return_value={
        "added": ["Central High", "Lincoln High"]
    })
    service.sports_collection = AsyncMock()
    service.sports_collection.find_one.return_value = {
        "teams": [
            {"team_id": 1, "team_name": "Central High"},
            {"team_id": 2, "team_name": "Lincoln High"},
        ]
    }
    service.sports_collection.update_one.return_value = SimpleNamespace(
        matched_count=1,
        modified_count=1,
    )
    service.games_collection = FakeGamesCollection()
    service._add_upload_metadata = AsyncMock(return_value=1)

    result = await service._ingest_games(
        "basketball",
        "mens",
        "high_school",
        "week.csv",
        b"2026-01-15,Central High,Lincoln High,72,68,0\n",
    )

    assert result["games_added"] == 1
    assert result["teams_added"] == ["Central High", "Lincoln High"]
    service.add_teams_to_db.assert_awaited_once()
    assert service.games_collection.inserted[0]["identity"] == (
        "2026-01-15|1|2"
    )
    assert service.games_collection.inserted[0]["game_id"] == (
        "1_2_2026-01-15"
    )
    stored_args = service._add_upload_metadata.await_args.args
    assert stored_args[0] == {
        "sport_type": "basketball",
        "gender": "mens",
        "level": "high_school",
    }
    assert stored_args[2] == "week.csv"
    assert stored_args[4] == 1
    stored_file = tmp_path / stored_args[3]
    assert stored_file.read_text() == (
        "2026-01-15,Central High,Lincoln High,72,68,0\n"
    )


@pytest.mark.asyncio
async def test_ingestion_rejects_a_game_already_in_storage(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))
    service = AdminTeamsService(("basketball", "mens", "high_school"))
    service._ingest_lock = asyncio.Lock()
    identity = canonical_game_identity("2026-01-15", 1, 2)
    service.find_missing_teams = AsyncMock(return_value=[])
    service.add_teams_to_db = AsyncMock(return_value={"added": []})
    service.sports_collection = AsyncMock()
    service.sports_collection.find_one.return_value = {
        "teams": [
            {"team_id": 1, "team_name": "Central High"},
            {"team_id": 2, "team_name": "Lincoln High"},
        ]
    }
    service.games_collection = FakeGamesCollection([
        {"identity": identity}
    ])
    service._add_upload_metadata = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await service._ingest_games(
            "basketball",
            "mens",
            "high_school",
            "week.csv",
            b"2026-01-15,Central High,Lincoln High,72,68,0\n",
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["duplicates"] == [
        "2026-01-15: Central High vs Lincoln High"
    ]
    service.add_teams_to_db.assert_not_awaited()
    service._add_upload_metadata.assert_not_awaited()
