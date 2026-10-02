from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest

from api.utils.algorithm.run import MainAlgorithm


def game_record():
    return {
        "game_id": "1_2_2026-01-15",
        "game_date": "2026-01-15",
        "home_team_id": 1,
        "home_team": "Team A",
        "away_team_id": 2,
        "away_team": "Team B",
        "home_score": 72,
        "away_score": 68,
        "neutral_site": 0,
    }


def team_document():
    return {
        "teams": [
            {
                "team_id": 1,
                "team_name": "Team A",
                "division": "1A",
                "power_ranking": [{"initial": 100.0}, {"old": 105.0}],
                "recent_opp": [2, 0, 0, 0, 0],
            },
            {
                "team_id": 2,
                "team_name": "Team B",
                "division": "1A",
                "power_ranking": [{"initial": 90.0}, {"old": 85.0}],
                "recent_opp": [1, 0, 0, 0, 0],
            },
        ]
    }


@pytest.fixture
def algorithm():
    sports_collection = SimpleNamespace(
        find_one=AsyncMock(return_value=team_document())
    )
    service = SimpleNamespace(
        retrieve_games=AsyncMock(return_value=[game_record()]),
        sports_collection=sports_collection,
        games_collection=MagicMock(),
        level_key=("basketball", "mens", "high_school"),
        level_constant={
            "_id": "dataset-id",
            "k_value": 0.43,
            "home_advantage": 4.5,
            "average_game_score": 106,
        },
    )
    return MainAlgorithm(service, ("basketball", "mens", "high_school"))


@pytest.mark.asyncio
async def test_load_games_uses_canonical_mongo_records(algorithm):
    games = await algorithm.load_games()
    frame = algorithm.games_dataframe(games)

    assert list(frame.columns) == [
        "date",
        "home_team",
        "away_team",
        "home_score",
        "away_score",
        "neutral_site",
    ]
    assert frame.iloc[0].to_dict() == {
        "date": "2026-01-15",
        "home_team": "Team A",
        "away_team": "Team B",
        "home_score": 72,
        "away_score": 68,
        "neutral_site": 0,
    }


@pytest.mark.asyncio
async def test_new_season_starts_from_power_preserved_at_reset(algorithm):
    document = team_document()
    document["teams"][0]["season_initial_power"] = {
        "2025-12-31": 105.0
    }
    algorithm.team_services.sports_collection.find_one.return_value = document

    teams = await algorithm.retrieve_teams(use_initial=True)

    assert teams[0]["initial_power_ranking"] == 105.0
    assert teams[0]["power_ranking"] == [105.0]
    assert teams[1]["initial_power_ranking"] == 90.0


@pytest.mark.asyncio
async def test_ranking_run_recomputes_then_persists_rankings_and_z_scores(
    algorithm,
):
    algorithm.clean_data = MagicMock(side_effect=lambda frame: frame)
    algorithm.enrich_data = MagicMock(side_effect=lambda frame, *_args: frame)
    algorithm.run_calculations = MagicMock(
        side_effect=lambda frame, teams: (frame, teams)
    )
    algorithm.output_to_db = AsyncMock()
    algorithm.calculate_z_scores = MagicMock(
        side_effect=lambda frame, _n: frame.assign(
            home_z_score=1.0,
            away_z_score=-1.0,
        )
    )
    algorithm.set_z_scores = AsyncMock()

    await algorithm.execute_algo(2)

    algorithm.team_services.retrieve_games.assert_awaited_once()
    assert algorithm.run_calculations.call_count == 2
    algorithm.output_to_db.assert_awaited_once()
    algorithm.set_z_scores.assert_awaited_once()
    persisted_frame = algorithm.output_to_db.await_args.args[0]
    assert isinstance(persisted_frame, pd.DataFrame)
    assert algorithm.output_to_db.await_args.args[-1] == "2026-01-15"


@pytest.mark.asyncio
async def test_ranking_run_rejects_unbounded_iterations(algorithm):
    with pytest.raises(Exception, match="Iterations must be between 1 and 100"):
        await algorithm.execute_algo(0)
