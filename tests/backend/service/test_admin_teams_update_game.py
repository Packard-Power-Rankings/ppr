import csv
from copy import deepcopy
from io import StringIO
from types import SimpleNamespace

import pytest
from bson.binary import Binary

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


@pytest.mark.asyncio
async def test_update_game_updates_both_teams_records_and_csv():
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
    csv_content = (
        "2026-01-09,Northstar Academy,Cedar Valley,72,61,0\n"
    ).encode("utf-8")
    service.sports_collection = FakeCollection({
        **dataset_fields,
        "teams": teams,
    })
    service.csv_collection = FakeCollection({
        "_id": "csv-document",
        "sport_type": "basketball",
        "gender": "mens",
        "level": "high_school",
        "csv_files": [{"filename": "week.csv", "filedata": Binary(csv_content)}],
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

    filedata = service.csv_collection.document["csv_files"][0]["filedata"]
    rows = list(csv.reader(StringIO(bytes(filedata).decode("utf-8"))))
    assert rows == [
        ["2026-01-09", "Northstar Academy", "Cedar Valley", "60", "70", "0"]
    ]


@pytest.mark.asyncio
async def test_find_season_dates_returns_orientation_and_scores():
    service = AdminTeamsService(("basketball", "mens", "high_school"))
    service.sports_collection = FakeCollection({
        "teams": [
            {
                "team_id": 2,
                "team_name": "Cedar Valley",
                "season_opp": [
                    {
                        "game_id": "1_2_2026-01-09",
                        "game_date": "2026-01-09",
                        "opponent_id": 1,
                        "opponent_name": "Northstar Academy",
                        "home_team": 0,
                        "home_score": 72,
                        "away_score": 61,
                    }
                ],
            }
        ]
    })

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
