"""Controlled migration from legacy team_num values to canonical team_id values."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from api.database import sports_database
from api.service.game_ingestion import (
    canonical_game_id,
    canonical_game_identity,
    normalize_team_name,
)


class TeamIdMigrationError(ValueError):
    """Raised when legacy identifiers cannot be migrated without ambiguity."""


def _positive_id(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise TeamIdMigrationError(f"{label} must be a positive whole number")
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise TeamIdMigrationError(
            f"{label} must be a positive whole number"
        ) from exc
    if result <= 0:
        raise TeamIdMigrationError(f"{label} must be a positive whole number")
    return result


def _name_keys(team: dict[str, Any]) -> set[str]:
    return {
        normalize_team_name(team.get(field) or "").casefold()
        for field in ("team_name", "short_name", "long_name")
        if normalize_team_name(team.get(field) or "")
    }


def _identifier_maps(
    teams: list[dict[str, Any]],
) -> tuple[dict[int, int], dict[str, int], int]:
    old_to_new = {}
    name_to_id = {}
    canonical_ids = set()
    legacy_count = 0

    for index, team in enumerate(teams, start=1):
        old_id = _positive_id(team.get("team_id"), f"Team {index} team_id")
        if old_id in old_to_new:
            raise TeamIdMigrationError(f"Duplicate existing team_id {old_id}")

        has_legacy_id = "team_num" in team
        canonical_id = _positive_id(
            team.get("team_num") if has_legacy_id else old_id,
            f"Team {team.get('team_name') or index} canonical ID",
        )
        if canonical_id in canonical_ids:
            raise TeamIdMigrationError(
                f"Canonical team_id {canonical_id} would be duplicated"
            )

        old_to_new[old_id] = canonical_id
        canonical_ids.add(canonical_id)
        legacy_count += int(has_legacy_id)
        for name_key in _name_keys(team):
            existing = name_to_id.get(name_key)
            if existing is not None and existing != canonical_id:
                raise TeamIdMigrationError(
                    f"Team alias {name_key!r} identifies more than one team"
                )
            name_to_id[name_key] = canonical_id

    return old_to_new, name_to_id, legacy_count


def _id_for_name(
    name: Any,
    name_to_id: dict[str, int],
    fallback: Any,
    old_to_new: dict[int, int],
) -> int:
    name_key = normalize_team_name(name or "").casefold()
    if name_key and name_key in name_to_id:
        return name_to_id[name_key]
    old_id = _positive_id(fallback, f"Reference for {name or 'unknown team'}")
    return old_to_new.get(old_id, old_id)


def _transform_teams(
    source_teams: list[dict[str, Any]],
    old_to_new: dict[int, int],
    name_to_id: dict[str, int],
) -> list[dict[str, Any]]:
    teams = deepcopy(source_teams)
    for team in teams:
        team_id = _id_for_name(
            team.get("team_name"),
            name_to_id,
            team.get("team_id"),
            old_to_new,
        )
        team["team_id"] = team_id
        team.pop("team_num", None)

        for game in team.get("season_opp", []):
            opponent_id = _id_for_name(
                game.get("opponent_name"),
                name_to_id,
                game.get("opponent_id"),
                old_to_new,
            )
            game["opponent_id"] = opponent_id
            game_date = game.get("game_date") or game.get("date")
            if game_date:
                is_home = game.get("home_team") in (1, True, "1")
                home_id, away_id = (
                    (team_id, opponent_id) if is_home
                    else (opponent_id, team_id)
                )
                game["game_id"] = canonical_game_id(
                    game_date,
                    home_id,
                    away_id,
                )

        if isinstance(team.get("recent_opp"), list):
            team["recent_opp"] = [
                0 if opponent_id in (None, 0, "0")
                else old_to_new.get(
                    _positive_id(opponent_id, "recent opponent ID"),
                    _positive_id(opponent_id, "recent opponent ID"),
                )
                for opponent_id in team["recent_opp"]
            ]
    return teams


def build_dataset_migration(
    current_document: dict[str, Any],
    games: list[dict[str, Any]],
    flagged_document: dict[str, Any] | None,
    previous_document: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build and validate every replacement before any database write occurs."""
    source_teams = current_document.get("teams", [])
    old_to_new, name_to_id, legacy_count = _identifier_maps(source_teams)
    if not legacy_count:
        return {
            "legacy_teams": 0,
            "changed_team_ids": 0,
            "current": deepcopy(current_document),
            "games": deepcopy(games),
            "flagged": deepcopy(flagged_document),
            "previous": deepcopy(previous_document),
        }

    current = deepcopy(current_document)
    current["teams"] = _transform_teams(
        source_teams,
        old_to_new,
        name_to_id,
    )

    transformed_games = []
    old_game_ids = {}
    identities = set()
    for source_game in games:
        game = deepcopy(source_game)
        home_id = _id_for_name(
            game.get("home_team"),
            name_to_id,
            game.get("home_team_id"),
            old_to_new,
        )
        away_id = _id_for_name(
            game.get("away_team"),
            name_to_id,
            game.get("away_team_id"),
            old_to_new,
        )
        game_date = game.get("game_date")
        identity = canonical_game_identity(game_date, home_id, away_id)
        if identity in identities:
            raise TeamIdMigrationError(
                f"Canonical game identity {identity} would be duplicated"
            )
        identities.add(identity)
        old_game_id = game.get("game_id")
        game["home_team_id"] = home_id
        game["away_team_id"] = away_id
        game["identity"] = identity
        game["game_id"] = canonical_game_id(game_date, home_id, away_id)
        if old_game_id:
            old_game_ids[str(old_game_id)] = game["game_id"]
        transformed_games.append(game)

    flagged = deepcopy(flagged_document)
    if flagged:
        for game in flagged.get("flagged_games", []):
            game["team1_id"] = _id_for_name(
                game.get("team1_name"),
                name_to_id,
                game.get("team1_id"),
                old_to_new,
            )
            game["team2_id"] = _id_for_name(
                game.get("team2_name"),
                name_to_id,
                game.get("team2_id"),
                old_to_new,
            )
            if game.get("game_id") in old_game_ids:
                game["game_id"] = old_game_ids[game["game_id"]]

    previous = deepcopy(previous_document)
    if previous:
        previous["teams"] = _transform_teams(
            previous.get("teams", []),
            old_to_new,
            name_to_id,
        )

    return {
        "legacy_teams": legacy_count,
        "changed_team_ids": sum(
            old_id != new_id for old_id, new_id in old_to_new.items()
        ),
        "current": current,
        "games": transformed_games,
        "flagged": flagged,
        "previous": previous,
    }


async def migrate_legacy_team_ids(apply: bool = False) -> dict[str, Any]:
    """Preflight or apply legacy identifier migration for every affected dataset."""
    current_collection = sports_database.get_collection("temp2")
    games_collection = sports_database.get_collection("games")
    flagged_collection = sports_database.get_collection("flagged_games")
    previous_collection = sports_database.get_collection("previous_season")

    cursor = current_collection.find({"teams.team_num": {"$exists": True}})
    current_documents = await cursor.to_list(length=None)
    summary = {
        "mode": "apply" if apply else "dry-run",
        "datasets": 0,
        "legacy_teams": 0,
        "changed_team_ids": 0,
        "games": 0,
        "flagged_games": 0,
        "previous_season_teams": 0,
    }

    for current_document in current_documents:
        dataset_query = {
            key: current_document[key]
            for key in ("sport_type", "gender", "level")
        }
        games = await games_collection.find(dataset_query).to_list(length=None)
        flagged = await flagged_collection.find_one(dataset_query)
        previous = await previous_collection.find_one(dataset_query)
        plan = build_dataset_migration(
            current_document,
            games,
            flagged,
            previous,
        )

        summary["datasets"] += 1
        summary["legacy_teams"] += plan["legacy_teams"]
        summary["changed_team_ids"] += plan["changed_team_ids"]
        summary["games"] += len(plan["games"])
        summary["flagged_games"] += len(
            (plan["flagged"] or {}).get("flagged_games", [])
        )
        summary["previous_season_teams"] += len(
            (plan["previous"] or {}).get("teams", [])
        )

        if not apply:
            continue

        for game in plan["games"]:
            migration_key = f"team-id-migration:{game['_id']}"
            await games_collection.update_one(
                {"_id": game["_id"]},
                {"$set": {
                    "identity": migration_key,
                    "game_id": migration_key,
                }},
            )
        for game in plan["games"]:
            await games_collection.replace_one({"_id": game["_id"]}, game)
        if plan["flagged"]:
            await flagged_collection.replace_one(
                {"_id": plan["flagged"]["_id"]},
                plan["flagged"],
            )
        if plan["previous"]:
            await previous_collection.replace_one(
                {"_id": plan["previous"]["_id"]},
                plan["previous"],
            )
        await current_collection.replace_one(
            {"_id": plan["current"]["_id"]},
            plan["current"],
        )

    return summary
