import base64
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
    csv_content = (
        "2026-01-01,Northstar Academy,Cedar Valley,80,70,0\n"
        "2026-01-02,Cedar Valley,Northstar Academy,65,75,0\n"
    ).encode("utf-8")
    service.sports_collection = FakeCollection({
        **dataset_fields,
        "teams": deepcopy(teams),
    })
    service.csv_collection = FakeCollection({
        "_id": "csv-document",
        **{key: value for key, value in dataset_fields.items() if key != "_id"},
        "csv_files": [{"filename": "week.csv", "filedata": Binary(csv_content)}],
    })
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
        "csv_replacements": 2,
        "csv_files": 1,
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

    csv_filedata = service.csv_collection.document["csv_files"][0]["filedata"]
    csv_rows = list(csv.reader(StringIO(bytes(csv_filedata).decode("utf-8"))))
    assert csv_rows[0][1] == "Northstar Prep"
    assert csv_rows[1][2] == "Northstar Prep"

    flagged_game = service.flagged_games.document["flagged_games"][0]
    assert flagged_game["team1_name"] == "Northstar Prep"
    assert "Northstar Prep" in flagged_game["game_id"]
    archived_teams = service.previous_season.document["teams"]
    assert archived_teams[0]["team_name"] == "Northstar Prep"
    assert archived_teams[1]["season_opp"][0]["opponent_name"] == "Northstar Prep"
    assert "Northstar Prep" in archived_teams[1]["season_opp"][0]["game_id"]


def test_rename_team_rows_in_csv_supports_legacy_base64_data():
    csv_content = (
        "2026-01-01,Northstar Academy,Cedar Valley,80,70,0\n"
    ).encode("utf-8")
    legacy_filedata = base64.b64encode(csv_content).decode("utf-8")

    updated_filedata, replacements = \
        AdminTeamsService._rename_team_rows_in_csv(
            legacy_filedata,
            {"Northstar Academy"},
            "Northstar Prep"
        )
    rows = list(csv.reader(StringIO(bytes(updated_filedata).decode("utf-8"))))

    assert replacements == 1
    assert rows[0][1] == "Northstar Prep"
