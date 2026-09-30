import json

import pytest
from fastapi import HTTPException

from api.service.archive_service import ArchiveService


class FakeCursor:
    def __init__(self, documents):
        self.documents = documents

    async def to_list(self, length=None):
        return self.documents


class FakeCollection:
    def __init__(self, documents):
        self.documents = documents

    def find(self, _query, _projection):
        return FakeCursor(self.documents)


@pytest.mark.asyncio
async def test_archive_writes_ranked_public_pages_and_catalog(tmp_path):
    collection = FakeCollection([
        {
            "sport_type": "basketball",
            "gender": "mens",
            "level": "high_school",
            "teams": [
                {
                    "team_id": 2,
                    "overall_rank": 2,
                    "team_name": "Cedar Valley",
                    "power_ranking": [{"2026-02-01": 48.1}],
                    "division_rank": 2,
                    "division": "5A",
                    "wins": 8,
                    "losses": 2,
                },
                {
                    "team_id": 1,
                    "overall_rank": 1,
                    "team_name": "Northstar <script>",
                    "power_ranking": [{"2026-02-01": 51.25}],
                    "division_rank": 1,
                    "division": "5A",
                    "wins": 10,
                    "losses": 0,
                },
            ],
        }
    ])
    service = ArchiveService(collection, tmp_path)

    result = await service.archive_current_season(2026)

    assert result["year"] == 2026
    assert result["dataset_count"] == 1
    assert result["team_count"] == 2
    assert result["overwritten"] is False

    data = json.loads((tmp_path / "2026" / "data.json").read_text())
    teams = data["datasets"][0]["teams"]
    assert [team["team_name"] for team in teams] == [
        "Northstar <script>",
        "Cedar Valley",
    ]
    assert [team["rank"] for team in teams] == [1, 2]

    static_page = (
        tmp_path / "2026" / "basketball-mens-high-school.html"
    ).read_text()
    assert "Northstar &lt;script&gt;" in static_page
    assert "Northstar <script>" not in static_page
    assert static_page.index("Northstar") < static_page.index("Cedar Valley")

    catalog = service.list_archives()
    assert catalog["archives"][0]["year"] == 2026
    assert catalog["archives"][0]["datasets"][0]["team_count"] == 2
    assert service.get_archive(2026)["team_count"] == 2


@pytest.mark.asyncio
async def test_archive_requires_explicit_overwrite(tmp_path):
    collection = FakeCollection([
        {
            "sport_type": "football",
            "gender": "mens",
            "level": "college",
            "teams": [{
                "team_id": 1,
                "team_name": "Original Team",
                "power_ranking": [{"2026-01-01": 10}],
            }],
        }
    ])
    service = ArchiveService(collection, tmp_path)
    await service.archive_current_season(2026)

    assert service.archive_status(2026) == {"year": 2026, "exists": True}
    with pytest.raises(HTTPException) as conflict:
        await service.archive_current_season(2026)
    assert conflict.value.status_code == 409

    collection.documents[0]["teams"][0]["team_name"] = "Replacement Team"
    result = await service.archive_current_season(2026, overwrite=True)

    assert result["overwritten"] is True
    assert service.get_archive(2026)["datasets"][0]["teams"][0][
        "team_name"
    ] == "Replacement Team"
