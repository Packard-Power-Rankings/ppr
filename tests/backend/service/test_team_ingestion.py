import pytest

from api.service.admin_teams import AdminTeamsService
from api.service.team_ingestion import TeamFileValidationError, parse_team_csv


def test_parse_team_csv_uses_required_headers_and_normalizes_values():
    teams = parse_team_csv(
        b"ranked,conference,long_name,short_name,state,division,ignored\n"
        b"yes,Great Northwest,,AK Anchorage,Alaska,NCAA 2,ignored value\n"
        b"no,,,AL Huntsville,Alabama,NAIA,ignored value\n"
    )

    assert teams == [
        {
            "state": "Alaska",
            "short_name": "AK Anchorage",
            "long_name": "",
            "division": "NCAA 2",
            "conference": "Great Northwest",
            "ranked": True,
        },
        {
            "state": "Alabama",
            "short_name": "AL Huntsville",
            "long_name": "",
            "division": "NAIA",
            "conference": "",
            "ranked": False,
        },
    ]


@pytest.mark.parametrize(
    ("content", "error"),
    [
        (b"state,short_name,division\n", "Missing required headers"),
        (
            b"state,short_name,long_name,division,conference,ranked\n"
            b"Alaska,,University,,Great Northwest,yes\n",
            "short_name is required",
        ),
        (
            b"state,short_name,long_name,division,conference,ranked\n"
            b"Alaska,Anchorage,,,Great Northwest,maybe\n",
            "ranked must be yes or no",
        ),
        (
            b"state,short_name,long_name,division,conference,ranked\n"
            b"Alaska,Anchorage,,,Great Northwest\n",
            "expected 6 columns",
        ),
    ],
)
def test_parse_team_csv_rejects_invalid_headers_or_rows(content, error):
    with pytest.raises(TeamFileValidationError, match=error):
        parse_team_csv(content)


class FakeTeamsCollection:
    def __init__(self, teams):
        self.document = {"teams": teams}

    async def update_one(self, _query, update, upsert=False):
        if "$push" in update:
            self.document["teams"].extend(update["$push"]["teams"]["$each"])
        return type("Result", (), {"modified_count": 1})()

    async def find_one(self, _query, _projection=None):
        return self.document


@pytest.mark.asyncio
async def test_import_skips_short_or_long_name_duplicates_and_stores_metadata():
    service = AdminTeamsService(("basketball", "womens", "college"))
    service.sports_collection = FakeTeamsCollection([
        {
            "team_id": 3,
            "team_name": "Northstar Academy",
            "short_name": "Northstar Academy",
            "long_name": "University of Northstar",
        },
        {
            "team_id": 8,
            "team_name": "Cedar Valley",
            "short_name": "Cedar Valley",
            "long_name": "Cedar University",
        },
    ])
    file_content = (
        b"state,short_name,long_name,division,conference,ranked\n"
        b"Washington,University of Northstar,,College,GNU,yes\n"
        b"Oregon,New Cedar,Cedar Valley,College,GNAC,no\n"
        b"Alaska,North Alaska,University of North Alaska,College,GNAC,yes\n"
        b"Alaska,North Alaska,,College,GNAC,no\n"
    )

    result = await service.import_team_csv("teams.csv", file_content)

    assert result["teams_added_count"] == 1
    assert result["teams_failed"] == [
        {
            "team_name": "University of Northstar",
            "reason": "A team with this short or long name already exists in the database",
        },
        {
            "team_name": "New Cedar",
            "reason": "A team with this short or long name already exists in the database",
        },
        {
            "team_name": "North Alaska",
            "reason": "Duplicate short or long name within the uploaded file",
        },
    ]
    new_team = service.sports_collection.document["teams"][-1]
    assert new_team["team_id"] == 9
    assert new_team["team_name"] == "North Alaska"
    assert new_team["short_name"] == "North Alaska"
    assert new_team["long_name"] == "University of North Alaska"
    assert new_team["state"] == "Alaska"
    assert new_team["division"] == "College"
    assert new_team["conference"] == "GNAC"
    assert new_team["ranked"] is True
