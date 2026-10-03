from types import SimpleNamespace
from unittest.mock import AsyncMock

import pandas as pd
import pytest

from api.utils.algorithm import output


@pytest.mark.asyncio
async def test_update_teams_persists_ranks_within_conferences(monkeypatch):
    monkeypatch.setattr(
        output,
        "UpdateOne",
        lambda filter_query, update: (filter_query, update),
    )
    collection = SimpleNamespace(
        bulk_write=AsyncMock(),
        update_one=AsyncMock(),
    )
    teams = [
        {
            "team_id": 1,
            "team_name": "East A",
            "overall_rank": 4,
            "division": "1A",
            "conference": "East",
            "power_ranking": [100.0],
            "recent_opp": [],
        },
        {
            "team_id": 2,
            "team_name": "West A",
            "overall_rank": 3,
            "division": "1A",
            "conference": "West",
            "power_ranking": [90.0],
            "recent_opp": [],
        },
        {
            "team_id": 3,
            "team_name": "East B",
            "overall_rank": 2,
            "division": "2A",
            "conference": "East",
            "power_ranking": [80.0],
            "recent_opp": [],
        },
        {
            "team_id": 4,
            "team_name": "West B",
            "overall_rank": 1,
            "division": "2A",
            "conference": "West",
            "power_ranking": [70.0],
            "recent_opp": [],
        },
    ]

    await output.update_teams(
        pd.DataFrame(), teams, collection, {"_id": "dataset-id"}, ""
    )

    operations = collection.bulk_write.await_args.args[0]
    ranks_by_team = {
        query["teams.team_id"]: update["$set"]
        for query, update in operations
    }
    assert ranks_by_team[1]["teams.$.conference_rank"] == 1
    assert ranks_by_team[2]["teams.$.conference_rank"] == 1
    assert ranks_by_team[3]["teams.$.conference_rank"] == 2
    assert ranks_by_team[4]["teams.$.conference_rank"] == 2
    assert all(
        "teams.$.last_rank" not in persisted_values
        for persisted_values in ranks_by_team.values()
    )
