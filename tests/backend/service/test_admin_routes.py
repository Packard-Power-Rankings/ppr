from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile

from api.routers import admin_routes
from api.schemas.items import InputMethod


PUBLIC_ADMIN_ROUTER_PATHS = {
    "/token/",
    "/logout/",
    "/validate-token/",
    "/setup/admin/",
    "/flagged-game",
    "/check-flagged/{game_id:path}",
}


class FakeGameService:
    def __init__(self):
        self.call = None

    async def store_csv(self, sport_type, gender, level, csv_file):
        self.call = (sport_type, gender, level, csv_file.filename)
        return {"games_added": 1}


def test_every_nonpublic_admin_route_requires_authentication():
    unprotected = [
        route.path
        for route in admin_routes.router.routes
        if route.path not in PUBLIC_ADMIN_ROUTER_PATHS and not route.dependencies
    ]

    assert unprotected == []


@pytest.mark.asyncio
async def test_game_upload_helper_delegates_to_ingestion_service(monkeypatch):
    service = FakeGameService()
    monkeypatch.setattr(admin_routes, "admin_team_class", lambda _key: service)
    sports_input = InputMethod(
        sport_type="basketball",
        gender="mens",
        level="high_school",
    )
    upload = UploadFile(
        file=BytesIO(b"2026-01-01,Home,Away,10,7,0\n"),
        filename="games.csv",
    )

    result = await admin_routes._store_uploaded_games(upload, sports_input)

    assert result == {"games_added": 1}
    assert tuple(getattr(value, "value", value) for value in service.call[:3]) == (
        "basketball",
        "mens",
        "high_school",
    )
    assert service.call[3] == "games.csv"


@pytest.mark.asyncio
async def test_team_upload_rejects_non_csv_file_before_parsing():
    sports_input = InputMethod(
        sport_type="basketball",
        gender="mens",
        level="high_school",
    )
    upload = UploadFile(file=BytesIO(b"not csv"), filename="teams.txt")

    with pytest.raises(HTTPException) as error:
        await admin_routes.upload_teams(upload, sports_input)

    assert error.value.status_code == 400
    assert error.value.detail == "Team file must be a CSV file"
