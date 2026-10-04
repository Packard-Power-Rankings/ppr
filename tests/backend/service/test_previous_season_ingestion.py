from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from api.service.admin_teams import AdminTeamsService
from api.service.previous_season_ingestion import (
    PreviousSeasonFileValidationError,
    parse_previous_season_csv,
)


HEADERS = (
    "team_id,wins,losses,"
    "ties,power,overall_rank,recent_opponent_1,recent_opponent_2,"
    "recent_opponent_3,recent_opponent_4,recent_opponent_5,div_rank\n"
)


def season_csv(*rows: str) -> bytes:
    return (HEADERS + "".join(f"{row}\n" for row in rows)).encode()


class FakeCollection:
    def __init__(self, document):
        self.document = document
        self.updates = []

    async def find_one(self, _query, _projection=None):
        return self.document

    async def update_one(self, query, update):
        self.updates.append((query, update))
        self.document.update(update["$set"])
        for field in update.get("$unset", {}):
            self.document.pop(field, None)
        return SimpleNamespace(matched_count=1, modified_count=1)


def test_parser_reads_only_required_fields_and_ignores_extra_columns():
    headers = HEADERS.rstrip().encode() + b",week_id,actual_change,total_score\n"
    row = (
        b"UCLA,37,1,0,425.5,1,49,2,62,23,8,1,"
        b"Game Set 168.1 2025 College Womens Basketball,1.5,0\n"
    )
    parsed = parse_previous_season_csv(headers + row)

    assert parsed.rows[0] == {
        "row_number": 2,
        "team_id": "UCLA",
        "wins": 37,
        "losses": 1,
        "ties": 0,
        "power": 425.5,
        "overall_rank": 1,
        "recent_opp": [49, 2, 62, 23, 8],
        "division_rank": 1,
    }


def test_parser_rejects_missing_required_headers():
    with pytest.raises(PreviousSeasonFileValidationError, match="Missing required"):
        parse_previous_season_csv(b"team_id,wins\nUCLA,37\n")


@pytest.mark.asyncio
async def test_import_matches_short_names_and_flags_unmatched_rows():
    service = AdminTeamsService(("basketball", "womens", "college"))
    service.sports_collection = FakeCollection({
        "games_revision": 4,
        "season_year": 2024,
        "week_id": "legacy-week",
        "source_week_id": "legacy-source-week",
        "source_year": 2023,
        "previous_season_import": {
            "source_week_id": "legacy-source-week",
            "source_year": 2023,
        },
        "teams": [
            {
                "team_id": 50,
                "team_name": "UCLA",
                "short_name": "UCLA",
                "week_id": "legacy-week",
                "actual_change": 12.5,
                "total_score": 900.0,
                "num_games": 20,
                "last_rank": 9,
                "win_ratio": 0.4,
                "long_name": "University of California Los Angeles",
                "season_opp": [{"game_id": "preserved"}],
                "season_initial_power": {"old": 300.0},
            },
            {
                "team_id": 2,
                "team_name": "Texas",
                "short_name": "Texas",
                "week_id": "legacy-week",
                "actual_change": 3.0,
                "total_score": 600.0,
                "num_games": 11,
            },
        ],
    })

    result = await service.import_previous_season_csv(
        "WomensCollegeBasketball.csv",
        season_csv(
            "UCLA,37,1,0,425.5,1,2,999,0,0,0,1",
            "Missing Team,10,2,0,300,2,0,0,0,0,0,2",
        ),
    )

    assert result["teams_updated_count"] == 1
    assert result["teams_flagged_count"] == 1
    assert result["flagged_teams"] == [{
        "row": 3,
        "team_id": "Missing Team",
        "reason": "No existing team has this short_name",
    }]
    assert result["warnings"] == [{
        "row": 2,
        "team_id": "UCLA",
        "reason": "Unknown recent opponent IDs were replaced with 0: 999",
    }]

    team = service.sports_collection.document["teams"][0]
    assert team["team_id"] == 50
    assert team["long_name"] == "University of California Los Angeles"
    assert not {"week_id", "actual_change",
                "total_score", "num_games"} & team.keys()
    assert team["last_rank"] == 9
    assert team["win_ratio"] == 0.4
    assert team["wins"] == 37
    assert team["losses"] == 1
    assert team["ties"] == 0
    assert team["power_ranking"] == [{result["snapshot_key"]: 425.5}]
    assert team["recent_opp"] == [2, 0, 0, 0, 0]
    assert team["season_opp"] == [{"game_id": "preserved"}]
    assert team["season_initial_power"] == {"old": 300.0}
    assert service.sports_collection.document["season_year"] == 2024
    assert not {
        "week_id",
        "source_week_id",
        "source_year",
    } & service.sports_collection.document.keys()
    assert "source_week_id" not in service.sports_collection.document[
        "previous_season_import"
    ]
    assert not {
        "week_id",
        "actual_change",
        "total_score",
        "num_games",
    } & service.sports_collection.document["teams"][1].keys()
    assert service.sports_collection.document["ranking_status"] == "current"
    assert service.sports_collection.document["ranked_revision"] == 4


@pytest.mark.asyncio
async def test_import_does_not_fall_back_to_team_name():
    service = AdminTeamsService(("basketball", "womens", "college"))
    service.sports_collection = FakeCollection({
        "teams": [{
            "team_id": 50,
            "team_name": "UCLA",
            "short_name": "UCLA Bruins",
        }],
    })

    result = await service.import_previous_season_csv(
        "WomensCollegeBasketball.csv",
        season_csv(
            "UCLA,37,1,0,425.5,1,0,0,0,0,0,1"
        ),
    )

    assert result["teams_updated_count"] == 0
    assert result["teams_flagged_count"] == 1
    assert service.sports_collection.updates == []


@pytest.mark.asyncio
async def test_import_requires_teams_to_exist_first():
    service = AdminTeamsService(("basketball", "womens", "college"))
    service.sports_collection = FakeCollection({"teams": []})

    with pytest.raises(HTTPException) as error:
        await service.import_previous_season_csv(
            "WomensCollegeBasketball.csv",
            season_csv(
                "UCLA,37,1,0,425.5,1,0,0,0,0,0,1"
            ),
        )

    assert error.value.status_code == 409
    assert "Import the team data" in error.value.detail
