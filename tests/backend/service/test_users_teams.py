import pytest
from fastapi import HTTPException

from api.service.users_teams import UsersServices


class FakeCursor:
    def __init__(self, result):
        self.result = result
        self.requested_length = None

    async def to_list(self, length):
        self.requested_length = length
        return self.result


class FakeUserCollection:
    def __init__(self, aggregate_result=None, team_result=None):
        self.aggregate_result = aggregate_result or []
        self.team_result = team_result
        self.pipeline = None
        self.query = None
        self.cursor = None

    def aggregate(self, pipeline):
        self.pipeline = pipeline
        self.cursor = FakeCursor(self.aggregate_result)
        return self.cursor

    async def find_one(self, query, _projection):
        self.query = query
        return self.team_result


@pytest.mark.asyncio
async def test_team_lookup_escapes_regex_metacharacters():
    service = UsersServices(("basketball", "mens", "high_school"))
    collection = FakeUserCollection()
    service.user_collection = collection

    await service.retrieve_team_info(".*")

    name_match = collection.pipeline[2]["$match"]["teams.team_name"]
    assert name_match["$regex"] == r"^\.\*$"
    assert collection.cursor.requested_length == 1


@pytest.mark.asyncio
async def test_prediction_lookup_rejects_duplicate_or_missing_teams():
    service = UsersServices(("basketball", "mens", "high_school"))
    collection = FakeUserCollection()
    service.user_collection = collection

    with pytest.raises(HTTPException) as duplicate_error:
        await service._retrieve_team_info(["Same Team", "same team"])
    assert duplicate_error.value.status_code == 422

    with pytest.raises(HTTPException) as missing_error:
        await service._retrieve_team_info(["Home", "Away"])
    assert missing_error.value.status_code == 404
    assert collection.query["sport_type"] == "basketball"
    assert collection.query["gender"] == "mens"
    assert collection.query["level"] == "high_school"
