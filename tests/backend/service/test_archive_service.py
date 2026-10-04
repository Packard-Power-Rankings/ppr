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

    def find(self, query, _projection):
        documents = [
            document
            for document in self.documents
            if all(
                isinstance(expected, dict) or document.get(field) == expected
                for field, expected in query.items()
            )
        ]
        return FakeCursor(documents)


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
                    "team_id": 3,
                    "overall_rank": -1,
                    "team_name": "Unranked College",
                    "power_ranking": [{"2026-02-01": 30.0}],
                    "division_rank": -1,
                    "division": "Other",
                    "wins": 0,
                    "losses": 0,
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
    assert result["team_count"] == 3
    assert result["overwritten"] is False

    data = json.loads((tmp_path / "2026" / "data.json").read_text())
    teams = data["datasets"][0]["teams"]
    assert [team["team_name"] for team in teams] == [
        "Northstar <script>",
        "Cedar Valley",
        "Unranked College",
    ]
    assert [team["rank"] for team in teams] == [1, 2, 9999]

    static_page = (
        tmp_path / "2026" / "basketball-mens-high-school.html"
    ).read_text()
    assert "Northstar &lt;script&gt;" in static_page
    assert "Northstar <script>" not in static_page
    assert "<th>Rank</th>" in static_page
    assert '<th class="number">Power</th>' in static_page
    assert '<th class="number">Div. Rank</th>' in static_page
    assert "2026 High School Mens Basketball Rankings" in static_page
    assert static_page.index("Northstar") < static_page.index("Cedar Valley")

    catalog = service.list_archives()
    assert catalog["archives"][0]["year"] == 2026
    assert catalog["archives"][0]["datasets"][0]["team_count"] == 3
    assert service.get_archive(2026)["team_count"] == 3


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

    assert service.archive_status(2026) == {
        "year": 2026,
        "exists": True,
        "complete": True,
    }
    with pytest.raises(HTTPException) as conflict:
        await service.archive_current_season(2026)
    assert conflict.value.status_code == 409

    collection.documents[0]["teams"][0]["team_name"] = "Replacement Team"
    result = await service.archive_current_season(2026, overwrite=True)

    assert result["overwritten"] is True
    assert service.get_archive(2026)["datasets"][0]["teams"][0][
        "team_name"
    ] == "Replacement Team"


def test_archive_status_requires_readable_archive_data(tmp_path):
    service = ArchiveService(FakeCollection([]), tmp_path)
    (tmp_path / "2026").mkdir()

    assert service.archive_status(2026) == {
        "year": 2026,
        "exists": False,
        "complete": False,
    }

    (tmp_path / "2026" / "data.json").write_text(
        json.dumps({"year": 2026, "datasets": []}),
        encoding="utf-8",
    )

    assert service.archive_status(2026) == {
        "year": 2026,
        "exists": True,
        "complete": True,
    }


@pytest.mark.asyncio
async def test_selected_archive_merges_and_overwrites_only_selected_dataset(tmp_path):
    collection = FakeCollection([
        {
            "sport_type": "basketball",
            "gender": "mens",
            "level": "high_school",
            "teams": [{"team_id": 1, "team_name": "Northstar"}],
        },
        {
            "sport_type": "football",
            "gender": "mens",
            "level": "college",
            "teams": [{"team_id": 2, "team_name": "Mountain State"}],
        },
    ])
    service = ArchiveService(collection, tmp_path)
    basketball = ("basketball", "mens", "high_school")
    football = ("football", "mens", "college")

    first = await service.archive_current_season(2026, dataset_key=basketball)

    assert first["scope"] == "selected"
    assert first["overwritten"] is False
    assert service.archive_status(2026) == {
        "year": 2026,
        "exists": True,
        "complete": False,
    }
    assert service.archive_status(2026, basketball)["exists"] is True
    assert service.archive_status(2026, football)["exists"] is False

    await service.archive_current_season(2026, dataset_key=football)
    archive = service.get_archive(2026)
    assert [dataset["slug"] for dataset in archive["datasets"]] == [
        "football-mens-college",
        "basketball-mens-high-school",
    ]

    with pytest.raises(HTTPException) as conflict:
        await service.archive_current_season(2026, dataset_key=basketball)
    assert conflict.value.status_code == 409

    collection.documents[0]["teams"][0]["team_name"] = "Replacement Team"
    result = await service.archive_current_season(
        2026,
        overwrite=True,
        dataset_key=basketball,
    )

    assert result["overwritten"] is True
    archive = service.get_archive(2026)
    archived_by_slug = {
        dataset["slug"]: dataset
        for dataset in archive["datasets"]
    }
    assert archived_by_slug["basketball-mens-high-school"]["teams"][0][
        "team_name"
    ] == "Replacement Team"
    assert archived_by_slug["football-mens-college"]["teams"][0][
        "team_name"
    ] == "Mountain State"
