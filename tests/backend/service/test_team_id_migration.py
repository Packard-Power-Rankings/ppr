from api.service.team_id_migration import (
    build_dataset_migration,
    TeamIdMigrationError,
)

import pytest


def test_migration_rekeys_every_team_reference_and_removes_team_num():
    current = {
        "_id": "current",
        "sport_type": "basketball",
        "gender": "mens",
        "level": "college",
        "teams": [
            {
                "team_id": 1,
                "team_num": 713,
                "team_name": "AK Anchorage",
                "recent_opp": [0, 0, 0, 0, 2],
                "season_opp": [{
                    "opponent_id": 2,
                    "opponent_name": "AK Fairbanks",
                    "home_team": 1,
                    "game_date": "2026-01-15",
                    "game_id": "1_2_2026-01-15",
                }],
            },
            {
                "team_id": 2,
                "team_num": 714,
                "team_name": "AK Fairbanks",
                "recent_opp": [0, 0, 0, 0, 1],
                "season_opp": [{
                    "opponent_id": 1,
                    "opponent_name": "AK Anchorage",
                    "home_team": 0,
                    "game_date": "2026-01-15",
                    "game_id": "1_2_2026-01-15",
                }],
            },
        ],
    }
    games = [{
        "_id": "game",
        "game_date": "2026-01-15",
        "game_id": "1_2_2026-01-15",
        "identity": "2026-01-15|1|2",
        "home_team_id": 1,
        "home_team": "AK Anchorage",
        "away_team_id": 2,
        "away_team": "AK Fairbanks",
    }]
    flagged = {
        "_id": "flagged",
        "flagged_games": [{
            "game_id": "1_2_2026-01-15",
            "team1_id": 1,
            "team1_name": "AK Anchorage",
            "team2_id": 2,
            "team2_name": "AK Fairbanks",
        }],
    }
    previous = {
        "_id": "previous",
        "teams": [{
            "team_id": 1,
            "team_name": "AK Anchorage",
            "recent_opp": [2],
            "season_opp": [{
                "opponent_id": 2,
                "opponent_name": "AK Fairbanks",
                "home_team": 1,
                "game_date": "2025-01-15",
                "game_id": "1_2_2025-01-15",
            }],
        }],
    }

    plan = build_dataset_migration(current, games, flagged, previous)

    assert plan["legacy_teams"] == 2
    assert plan["changed_team_ids"] == 2
    assert [team["team_id"] for team in plan["current"]["teams"]] == [713, 714]
    assert all("team_num" not in team for team in plan["current"]["teams"])
    assert plan["current"]["teams"][0]["recent_opp"][-1] == 714
    assert plan["current"]["teams"][0]["season_opp"][0] == {
        "opponent_id": 714,
        "opponent_name": "AK Fairbanks",
        "home_team": 1,
        "game_date": "2026-01-15",
        "game_id": "713_714_2026-01-15",
    }
    assert plan["games"][0]["home_team_id"] == 713
    assert plan["games"][0]["away_team_id"] == 714
    assert plan["games"][0]["identity"] == "2026-01-15|713|714"
    assert plan["games"][0]["game_id"] == "713_714_2026-01-15"
    assert plan["flagged"]["flagged_games"][0]["game_id"] == (
        "713_714_2026-01-15"
    )
    assert plan["flagged"]["flagged_games"][0]["team1_id"] == 713
    assert plan["previous"]["teams"][0]["team_id"] == 713
    assert plan["previous"]["teams"][0]["season_opp"][0]["opponent_id"] == 714


def test_migration_rejects_duplicate_canonical_ids_before_writing():
    current = {
        "teams": [
            {"team_id": 1, "team_num": 713, "team_name": "Team A"},
            {"team_id": 2, "team_num": 713, "team_name": "Team B"},
        ],
    }

    with pytest.raises(
        TeamIdMigrationError,
        match="Canonical team_id 713 would be duplicated",
    ):
        build_dataset_migration(current, [], None, None)
