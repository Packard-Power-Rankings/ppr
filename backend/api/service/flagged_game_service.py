"""Administrative review workflow for publicly reported game issues."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from bson import ObjectId
from fastapi import HTTPException, status

from api.database import sports_database


LEGACY_ISSUE_DESCRIPTION = (
    "This report was created before issue descriptions were collected."
)


def _reported_at(document: dict[str, Any]) -> datetime:
    document_id = document.get("_id")
    if isinstance(document_id, ObjectId):
        return document_id.generation_time
    return datetime.now(timezone.utc)


async def migrate_legacy_flagged_games() -> None:
    """Add review metadata to reports created by older application versions."""
    collection = sports_database.get_collection("flagged_games")
    documents = await collection.find({}, {"flagged_games": 1}).to_list(length=None)
    for document in documents:
        issues = document.get("flagged_games", [])
        changed = False
        fallback_time = _reported_at(document)
        for issue in issues:
            if not issue.get("issue_id"):
                issue["issue_id"] = uuid4().hex
                changed = True
            if not issue.get("description"):
                issue["description"] = LEGACY_ISSUE_DESCRIPTION
                changed = True
            if not issue.get("reported_at"):
                issue["reported_at"] = fallback_time
                changed = True
            if not issue.get("status"):
                issue["status"] = "open"
                changed = True
        if changed:
            await collection.update_one(
                {"_id": document["_id"]},
                {"$set": {"flagged_games": issues}},
            )


class FlaggedGameService:
    def __init__(self) -> None:
        self.collection = sports_database.get_collection("flagged_games")

    @staticmethod
    def _open_issue_pipeline() -> list[dict[str, Any]]:
        return [
            {"$unwind": "$flagged_games"},
            {"$match": {"flagged_games.status": {"$ne": "resolved"}}},
        ]

    async def count_open_issues(self) -> int:
        pipeline = [
            *self._open_issue_pipeline(),
            {"$count": "count"},
        ]
        result = await self.collection.aggregate(pipeline).to_list(length=1)
        return int(result[0]["count"]) if result else 0

    async def list_open_issues(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        pipeline = [
            *self._open_issue_pipeline(),
            {"$project": {
                "_id": 0,
                "issue_id": "$flagged_games.issue_id",
                "game_id": "$flagged_games.game_id",
                "team1_id": "$flagged_games.team1_id",
                "team1_name": "$flagged_games.team1_name",
                "team2_id": "$flagged_games.team2_id",
                "team2_name": "$flagged_games.team2_name",
                "description": "$flagged_games.description",
                "reported_at": "$flagged_games.reported_at",
                "sport_type": 1,
                "gender": 1,
                "level": 1,
            }},
            {"$sort": {"reported_at": 1, "issue_id": 1}},
            {"$skip": skip},
            {"$limit": limit},
        ]
        issues = await self.collection.aggregate(pipeline).to_list(length=limit)
        for issue in issues:
            reported_at = issue.get("reported_at")
            if isinstance(reported_at, datetime):
                issue["reported_at"] = (
                    reported_at.replace(tzinfo=timezone.utc)
                    if reported_at.tzinfo is None
                    else reported_at.astimezone(timezone.utc)
                )
        return {
            "issues": issues,
            "count": await self.count_open_issues(),
            "skip": skip,
            "limit": limit,
        }

    async def resolve_issue(self, issue_id: str) -> dict[str, Any]:
        resolved_at = datetime.now(timezone.utc)
        result = await self.collection.update_one(
            {
                "flagged_games": {
                    "$elemMatch": {
                        "issue_id": issue_id,
                        "status": {"$ne": "resolved"},
                    }
                }
            },
            {"$set": {
                "flagged_games.$.status": "resolved",
                "flagged_games.$.resolved_at": resolved_at,
            }},
        )
        if not result.modified_count:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The flagged game issue was not found or is already resolved",
            )
        return {
            "message": "Flagged game issue resolved",
            "issue_id": issue_id,
            "resolved_at": resolved_at,
        }
