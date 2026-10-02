from bson import ObjectId
import pytest

from api.routers import admin_routes
from api.schemas.items import InputMethod
from api.service.admin_teams import AdminTeamsService
from api.config.constants import LEVEL_CONSTANTS


@pytest.mark.asyncio
async def test_get_all_teams_returns_full_unprojected_team_documents():
    team = {
        "team_id": 7,
        "team_name": "Northstar Academy",
        "ties": 1,
        "custom_stats": {"playoff_wins": 3},
    }

    class FakeCollection:
        async def find_one(self, query, projection):
            assert query == {"_id": LEVEL_CONSTANTS[(
                "football", "mens", "college")]["_id"]}
            assert projection == {"teams": 1, "_id": 0}
            return {"teams": [team]}

    service = AdminTeamsService.__new__(AdminTeamsService)
    service.level_constant = LEVEL_CONSTANTS[("football", "mens", "college")]
    service.sports_collection = FakeCollection()

    assert await service.get_all_teams() == [team]


@pytest.mark.asyncio
async def test_export_teams_route_uses_selected_dataset_and_encodes_all_fields(monkeypatch):
    team = {
        "team_id": 7,
        "team_name": "Northstar Academy",
        "custom_stats": {"playoff_wins": 3},
        "stored_id": ObjectId("67017efbb2d2f30e9c5ecc52"),
    }
    requested_datasets = []

    class FakeTeamService:
        async def get_all_teams(self):
            return [team]

    def fake_admin_team_class(level_key):
        requested_datasets.append(tuple(str(value) for value in level_key))
        return FakeTeamService()

    monkeypatch.setattr(admin_routes, "admin_team_class",
                        fake_admin_team_class)
    response = await admin_routes.export_teams(InputMethod(
        sport_type="football",
        gender="mens",
        level="college",
    ))

    assert requested_datasets == [("football", "mens", "college")]
    assert response == {
        "teams": [{
            "team_id": 7,
            "team_name": "Northstar Academy",
            "custom_stats": {"playoff_wins": 3},
            "stored_id": "67017efbb2d2f30e9c5ecc52",
        }],
    }
