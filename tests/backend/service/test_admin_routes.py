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


class FakeTeamService:
    def __init__(self):
        self.call = None

    async def import_team_csv(self, file_name, content):
        self.call = (file_name, content)
        return {"teams_added_count": 1}

    async def import_previous_season_csv(self, file_name, content):
        self.call = (file_name, content)
        return {"teams_updated_count": 1}


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


@pytest.mark.asyncio
async def test_team_upload_accepts_filename_matching_selected_dataset(monkeypatch):
    service = FakeTeamService()
    monkeypatch.setattr(admin_routes, "admin_team_class", lambda _key: service)
    sports_input = InputMethod(
        sport_type="basketball",
        gender="womens",
        level="college",
    )
    upload = UploadFile(
        file=BytesIO(b"team csv"),
        filename="WomensCollegeBasketBALL.csv",
    )

    result = await admin_routes.upload_teams(upload, sports_input)

    assert result == {"teams_added_count": 1}
    assert service.call == ("WomensCollegeBasketBALL.csv", b"team csv")


@pytest.mark.asyncio
async def test_team_upload_rejects_filename_for_different_dataset_before_import(monkeypatch):
    service = FakeTeamService()
    monkeypatch.setattr(admin_routes, "admin_team_class", lambda _key: service)
    sports_input = InputMethod(
        sport_type="basketball",
        gender="womens",
        level="college",
    )
    upload = UploadFile(
        file=BytesIO(b"team csv"),
        filename="MensCollegeFootball.csv",
    )

    with pytest.raises(HTTPException) as error:
        await admin_routes.upload_teams(upload, sports_input)

    assert error.value.status_code == 422
    assert "womens, college, basketball" in error.value.detail
    assert service.call is None


@pytest.mark.asyncio
async def test_team_upload_does_not_treat_women_filename_as_mens(monkeypatch):
    service = FakeTeamService()
    monkeypatch.setattr(admin_routes, "admin_team_class", lambda _key: service)
    sports_input = InputMethod(
        sport_type="basketball",
        gender="mens",
        level="college",
    )
    upload = UploadFile(
        file=BytesIO(b"team csv"),
        filename="WomenCollegeBasketBALL.csv",
    )

    with pytest.raises(HTTPException) as error:
        await admin_routes.upload_teams(upload, sports_input)

    assert error.value.status_code == 422
    assert service.call is None


@pytest.mark.asyncio
async def test_previous_season_upload_rejects_non_csv_file_before_parsing():
    sports_input = InputMethod(
        sport_type="basketball",
        gender="womens",
        level="college",
    )
    upload = UploadFile(file=BytesIO(b"not csv"), filename="season.txt")

    with pytest.raises(HTTPException) as error:
        await admin_routes.import_previous_season(upload, sports_input)

    assert error.value.status_code == 400
    assert error.value.detail == "Previous-season ranking file must be a CSV file"


@pytest.mark.asyncio
async def test_previous_season_upload_rejects_filename_not_matching_dataset(monkeypatch):
    service = FakeTeamService()
    monkeypatch.setattr(admin_routes, "admin_team_class", lambda _key: service)
    sports_input = InputMethod(
        sport_type="basketball",
        gender="womens",
        level="college",
    )
    upload = UploadFile(
        file=BytesIO(b"team_id,week_id"),
        filename="WomensCollegeFootball.csv",
    )

    with pytest.raises(HTTPException) as error:
        await admin_routes.import_previous_season(upload, sports_input)

    assert error.value.status_code == 422
    assert "womens, college, basketball" in error.value.detail
    assert service.call is None


@pytest.mark.asyncio
async def test_previous_season_upload_accepts_dataset_markers_in_any_case_and_order(
    monkeypatch,
):
    service = FakeTeamService()
    monkeypatch.setattr(admin_routes, "admin_team_class", lambda _key: service)
    sports_input = InputMethod(
        sport_type="basketball",
        gender="womens",
        level="college",
    )
    upload = UploadFile(
        file=BytesIO(b"team_id,week_id"),
        filename="BASKETBALL_college_WoMeN.csv",
    )

    result = await admin_routes.import_previous_season(upload, sports_input)

    assert result == {"teams_updated_count": 1}
    assert service.call == ("BASKETBALL_college_WoMeN.csv", b"team_id,week_id")
