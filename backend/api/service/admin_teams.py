"""Logical operations for Admin
"""


import asyncio
import binascii
import re
from typing import Any, List, Dict, Tuple
import traceback
import base64
from datetime import datetime, timezone
from fastapi import HTTPException, status, UploadFile
from pymongo import UpdateOne
from pymongo.errors import BulkWriteError, DuplicateKeyError
from api.config.constants import LEVEL_CONSTANTS
from api.database import sports_database as database
from api.service.game_ingestion import (
    canonical_game_id,
    canonical_game_identity,
    GameFileValidationError,
    GameRow,
    normalize_team_name,
    normalized_date,
    parse_game_csv,
    serialize_game_rows,
    validate_game_values,
)
from api.service.team_ingestion import parse_team_csv
from api.service.upload_storage import delete_game_file, store_game_file
from api.utils.json_helper import query_params_builder


class AdminTeamsService():
    """Admin Level CRUD operations for HTTP endpoints
    containing all the logic for operations with the
    database
    """

    def __init__(self, level_key: Tuple):
        """Initializes MongoDB connections, constants,
        and Child Class

        Args:
            level_key (Tuple): Tuple that contains three
            strings: sport_type, gender, level
        """
        self.sports_collection = database.get_collection('temp2')
        self.csv_collection = database.get_collection('csv_files')
        self.games_collection = database.get_collection('games')
        self.flagged_games = database.get_collection('flagged_games')
        self.previous_season = database.get_collection('previous_season')
        self.level_key = tuple(
            getattr(value, "value", value) for value in level_key
        )
        self.level_constant = LEVEL_CONSTANTS[self.level_key]
        self._ingest_lock = asyncio.Lock()
        # self.teams_check: List[Dict[str, str]] = []
        # self.main_algorithm = MainAlgorithm(self, level_key)

    async def store_csv(
        self,
        sport_type: str,
        gender: str,
        level: str,
        csv_file: UploadFile
    ):
        """Admin level http post method to handle CSV uploads and check for teams.

        Args:
            sport_type (str): Type Of Sport
            gender (str): Sport Gender
            level (str): Sport Level
            csv_file (UploadFile): CSV File to Store

        Raises:
            HTTPException: 422 Unprocessable Entity for formatting issues
            HTTPException: 400 Bad Request for other errors

        Returns:
            dict: Message and storage details for a successful game upload.
        """
        file_name = csv_file.filename or "games.csv"
        if not file_name.lower().endswith(".csv"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Game file must be a CSV file",
            )
        file_content = await csv_file.read()
        return await self._ingest_games(
            sport_type,
            gender,
            level,
            file_name,
            file_content,
        )

    async def store_game(
        self,
        sport_type: str,
        gender: str,
        level: str,
        game_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Store one manually entered game through the CSV-backed workflow."""
        values = [game_data[column] for column in (
            "date",
            "home_team",
            "away_team",
            "home_score",
            "away_score",
            "neutral_site",
        )]
        try:
            game = validate_game_values(values)
        except GameFileValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={"message": "Game validation failed",
                        "errors": exc.errors},
            ) from exc

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        return await self._ingest_games(
            sport_type,
            gender,
            level,
            f"manual-game-{timestamp}.csv",
            serialize_game_rows([game]),
        )

    async def _ingest_games(
        self,
        sport_type: str,
        gender: str,
        level: str,
        file_name: str,
        file_content: bytes,
    ) -> Dict[str, Any]:
        """Validate, deduplicate, resolve known teams, and store game rows."""
        try:
            games = parse_game_csv(file_content)
        except GameFileValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": "Game file validation failed",
                    "errors": exc.errors,
                },
            ) from exc

        async with self._ingest_lock:
            return await self._commit_games(
                sport_type,
                gender,
                level,
                file_name,
                games,
            )

    async def _commit_games(
        self,
        sport_type: str,
        gender: str,
        level: str,
        file_name: str,
        games: List[GameRow],
    ) -> Dict[str, Any]:
        """Write normalized games and filesystem upload metadata."""
        sport_type, gender, level = (
            getattr(value, "value", value)
            for value in (sport_type, gender, level)
        )
        team_names = []
        for game in games:
            team_names.extend((game.home_team, game.away_team))
        missing_teams = await self.find_missing_teams(team_names)
        if missing_teams:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "message": (
                        "Import team data before adding games. The game file "
                        "contains unknown teams."
                    ),
                    "unknown_teams": missing_teams,
                    "errors": [
                        f"Unknown team: {team_name}"
                        for team_name in missing_teams
                    ],
                },
            )

        dataset_query = {
            "sport_type": sport_type,
            "gender": gender,
            "level": level,
        }
        game_documents = await self._build_game_documents(
            games,
            dataset_query,
        )
        identities = [game["identity"] for game in game_documents]
        existing = await self.games_collection.find(
            {**dataset_query, "identity": {"$in": identities}},
            {"identity": 1},
        ).to_list(length=None)
        existing_identities = {game["identity"] for game in existing}
        if existing_identities:
            duplicates = [
                f"{game.date}: {game.home_team} vs {game.away_team}"
                for game, document in zip(games, game_documents)
                if document["identity"] in existing_identities
            ]
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "One or more games already exist",
                    "duplicates": duplicates,
                },
            )

        reference_content = serialize_game_rows(games)
        upload_id, storage_path = store_game_file(
            tuple(getattr(value, "value", value) for value in (
                sport_type,
                gender,
                level,
            )),
            file_name,
            reference_content,
        )
        now = datetime.now(timezone.utc)
        for document in game_documents:
            document.update({
                "source_upload_id": upload_id,
                "source_filename": file_name,
                "created_at": now,
                "updated_at": now,
            })

        try:
            await self.games_collection.insert_many(game_documents, ordered=True)
            files_uploaded = await self._add_upload_metadata(
                dataset_query,
                upload_id,
                file_name,
                storage_path,
                len(game_documents),
                game_documents[0]["game_date"],
                now,
            )
            await self.sports_collection.update_one(
                {"_id": self.level_constant.get("_id")},
                {"$set": {"rankings_stale": True}},
            )
        except (BulkWriteError, DuplicateKeyError) as exc:
            await self.games_collection.delete_many({
                **dataset_query,
                "source_upload_id": upload_id,
            })
            await self.csv_collection.update_one(
                dataset_query,
                {"$pull": {"csv_files": {"upload_id": upload_id}}},
            )
            delete_game_file(storage_path)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"message": "One or more games already exist"},
            ) from exc
        except Exception:
            await self.games_collection.delete_many({
                **dataset_query,
                "source_upload_id": upload_id,
            })
            await self.csv_collection.update_one(
                dataset_query,
                {"$pull": {"csv_files": {"upload_id": upload_id}}},
            )
            delete_game_file(storage_path)
            raise

        display_gender = getattr(gender, "value", gender)
        display_level = getattr(level, "value", level)
        display_sport = getattr(sport_type, "value", sport_type)
        return {
            "message": (
                f"Added {len(games)} game{'s' if len(games) != 1 else ''}"
                f" to {display_gender} {display_level} {display_sport}"
            ),
            "status": status.HTTP_200_OK,
            "files_uploaded": files_uploaded,
            "games_added": len(games),
        }

    async def _build_game_documents(
        self,
        games: List[GameRow],
        dataset_query: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Resolve validated rows to stable team IDs and canonical documents."""
        team_document = await self.sports_collection.find_one(
            {"_id": self.level_constant.get("_id")},
            {"teams.team_id": 1, "teams.team_name": 1},
        )
        teams = team_document.get("teams", []) if team_document else []
        teams_by_name = {
            normalize_team_name(team.get("team_name", "")).casefold(): team
            for team in teams
        }
        documents = []
        for game in games:
            home_team = teams_by_name.get(game.home_team.casefold())
            away_team = teams_by_name.get(game.away_team.casefold())
            if not home_team or not away_team:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="A validated game could not be matched to its teams",
                )
            game_date = normalized_date(game.date)
            home_team_id = int(home_team["team_id"])
            away_team_id = int(away_team["team_id"])
            documents.append({
                **dataset_query,
                "identity": canonical_game_identity(
                    game_date,
                    home_team_id,
                    away_team_id,
                ),
                "game_id": canonical_game_id(
                    game_date,
                    home_team_id,
                    away_team_id,
                ),
                "game_date": game_date,
                "home_team_id": home_team_id,
                "home_team": home_team["team_name"],
                "away_team_id": away_team_id,
                "away_team": away_team["team_name"],
                "home_score": game.home_score,
                "away_score": game.away_score,
                "neutral_site": game.neutral_site,
                "home_z_score": 0.0,
                "away_z_score": 0.0,
            })
        return documents

    async def find_missing_teams(
        self,
        teams: List[str]
    ):
        query_base = {
            "_id": self.level_constant.get('_id'),
            "sport_type": self.level_key[0],
            "gender": self.level_key[1],
            "level": self.level_key[2],
        }

        try:
            documents = await self.sports_collection.find(
                query_base,
                {"teams.team_name": 1},
            ).to_list(length=None)
            found_team_names = {
                str(team["team_name"]).strip().casefold()
                for doc in documents
                for team in doc.get("teams", [])
                if team.get("team_name")
            }
            missing_teams = []
            seen = set()
            for team_name in teams:
                clean_name = " ".join(str(team_name).split())
                normalized_name = clean_name.casefold()
                if (
                    clean_name
                    and normalized_name not in found_team_names
                    and normalized_name not in seen
                ):
                    missing_teams.append(clean_name)
                    seen.add(normalized_name)
            return missing_teams
        except Exception as exc:
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An internal error has occurred."
            ) from exc

    async def add_teams_to_db(
        self,
        teams: List[Dict[str, Any]],
    ) -> Any:
        """Adds new teams data to database

        Args:
            teams (List[Dict[str, Any]]): List of new teams to add 

        Returns:
            Any: Successful storage of new teams or an
            that the team already exists in the db
        """
        base_filter = {"_id": self.level_constant.get('_id')}
        await self.sports_collection.update_one(
            base_filter,
            {
                "$setOnInsert": {
                    "sport_type": self.level_key[0],
                    "gender": self.level_key[1],
                    "level": self.level_key[2],
                    "teams": [],
                }
            },
            upsert=True,
        )
        document = await self.sports_collection.find_one(
            base_filter,
            {
                "teams.team_id": 1,
                "teams.team_name": 1,
                "teams.short_name": 1,
                "teams.long_name": 1,
            },
        )
        existing_teams = document.get("teams", []) if document else []
        existing_team_ids = {
            int(team["team_id"])
            for team in existing_teams
            if isinstance(team.get("team_id"), int)
            and not isinstance(team.get("team_id"), bool)
        }
        existing_names = set()
        for existing_team in existing_teams:
            for name_field in ("team_name", "short_name", "long_name"):
                name = normalize_team_name(existing_team.get(name_field) or "")
                if name:
                    existing_names.add(name.casefold())
        preexisting_names = set(existing_names)
        preexisting_team_ids = set(existing_team_ids)
        added, skipped, new_teams = [], [], []
        for team in teams:
            short_name = normalize_team_name(
                team.get("short_name") or team.get("team_name") or ""
            )
            long_name = normalize_team_name(team.get("long_name") or "")
            team_name = short_name
            aliases = {
                name.casefold() for name in (short_name, long_name) if name
            }
            if not short_name:
                skipped.append({
                    "team_name": team.get("team_name") or "",
                    "reason": "Team name is required",
                })
                continue
            raw_team_id = team.get("team_id")
            if (
                not isinstance(raw_team_id, int)
                or isinstance(raw_team_id, bool)
                or raw_team_id <= 0
            ):
                skipped.append({
                    "team_name": team_name,
                    "reason": "A positive whole-number team_id is required",
                })
                continue
            team_id = raw_team_id
            if team_id in existing_team_ids:
                reason = (
                    f"Team ID {team_id} already exists in the database"
                    if team_id in preexisting_team_ids
                    else f"Duplicate team ID {team_id} within the request"
                )
                skipped.append({"team_name": team_name, "reason": reason})
                continue
            matched_aliases = aliases.intersection(existing_names)
            if matched_aliases:
                reason = (
                    "A team with this short or long name already exists in the database"
                    if matched_aliases.intersection(preexisting_names)
                    else "Duplicate short or long name within the uploaded file"
                )
                skipped.append({"team_name": team_name, "reason": reason})
                existing_names.update(aliases)
                continue
            try:
                initial_ranking = float(team.get("power_ranking", 0.0) or 0.0)
            except (TypeError, ValueError):
                initial_ranking = 0.0
            new_team_data = {
                "team_id": team_id,
                "team_name": team_name,
                "short_name": short_name,
                "long_name": long_name,
                "city": "",
                "state": team.get('state'),
                "division": team.get('division'),
                "conference": team.get('conference'),
                "ranked": bool(team.get("ranked", False)),
                "division_rank": 0,
                "conference_rank": 0,
                "overall_rank": 0,
                "last_rank": 0,
                "power_ranking": [{"initial": initial_ranking}],
                "win_ratio": 0.0,
                "wins": 0,
                "losses": 0,
                "date": "",
                "recent_opp": [0, 0, 0, 0, 0],
                "season_opp": []
            }
            new_teams.append(new_team_data)
            added.append(team_name)
            existing_team_ids.add(team_id)
            existing_names.update(aliases)
        if new_teams:
            result = await self.sports_collection.update_one(
                base_filter,
                {"$push": {"teams": {"$each": new_teams}}},
            )
            if result.modified_count == 0:
                added = []
        response_message = {
            "status": status.HTTP_200_OK,
            "added": added,
            "skipped": skipped
        }
        if added:
            response_message["message"] = "Teams were added successfully"
        elif skipped:
            response_message["message"] = "Teams already exist in the database"
        else:
            response_message["message"] = "No teams were processed"
        return response_message

    async def import_team_csv(
        self,
        file_name: str,
        file_content: bytes,
    ) -> Dict[str, Any]:
        """Validate and store team records from a header-based CSV file."""
        if not file_name.lower().endswith(".csv"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Team data file must be a CSV file",
            )

        imported_teams = parse_team_csv(file_content)
        async with self._ingest_lock:
            result = await self.add_teams_to_db([
                {
                    **team,
                    "team_name": team["short_name"],
                }
                for team in imported_teams
            ])
        added = result.get("added", [])
        failed = result.get("skipped", [])
        return {
            "message": (
                f"Added {len(added)} team{'s' if len(added) != 1 else ''}; "
                f"failed to add {len(failed)} team{'s' if len(failed) != 1 else ''}."
            ),
            "teams_added_count": len(added),
            "teams_failed": failed,
        }

    async def run_main_algorithm(self, iterations: int):
        """Runs the main algorithm

        Args:
            iterations (int): Number of times to run
            the algorithm
        """
        from api.utils.algorithm.run import MainAlgorithm
        algorithm = MainAlgorithm(self, self.level_key)
        await algorithm.execute_algo(iterations)

    async def calculate_z_scores(self):
        """Calculates z scores from the potential power changes
        """
        from api.utils.algorithm.run import MainAlgorithm
        z_scores = MainAlgorithm(self, self.level_key)
        await z_scores.execute_z_score_calc()

    async def update_db_data(
        self,
        home_team: str,
        home_score: int,
        away_team: str,
        away_score: int,
        game_id: str
    ):
        """Updates teams scores in the csv file as well as
        the teams in the database along with the wins/losses

        Args:
            home_team (str): Name of home team
            home_score (int): Home team Score
            away_team (str): Name of away team
            away_score (int): Away team Score
            game_id (str): Game ID based on 
        """
        dataset_filter = {"_id": self.level_constant.get("_id")}
        home_team_data = await self.sports_collection.find_one(
            {
                **dataset_filter,
                "teams.team_name": home_team,
                "teams.season_opp.game_id": game_id,
            },
            {"teams.$": 1}
        )

        away_team_data = await self.sports_collection.find_one(
            {
                **dataset_filter,
                "teams.team_name": away_team,
                "teams.season_opp.game_id": game_id,
            },
            {"teams.$": 1}
        )

        current_home_score = \
            home_team_data['teams'][0]['season_opp'][0]['home_score']
        current_away_score = \
            away_team_data['teams'][0]['season_opp'][0]['away_score']

        current_home_wins = \
            home_team_data['teams'][0]['wins']
        current_home_losses = \
            home_team_data['teams'][0]['losses']
        current_away_wins = \
            away_team_data['teams'][0]['wins']
        current_away_losses = \
            away_team_data['teams'][0]['losses']

        home_won_current = current_home_score > current_away_score
        home_won_now = home_score > away_score

        if home_won_current != home_won_now:
            update_home_wins = \
                current_home_wins + (1 if home_won_now else -1)
            updated_home_losses = \
                current_home_losses + (-1 if home_won_now else 1)
            updated_away_wins = \
                current_away_wins + (-1 if home_won_now else 1)
            updated_away_losses = \
                current_away_losses + (1 if home_won_now else -1)

            await self.sports_collection.find_one_and_update(
                {
                    **dataset_filter,
                    "teams.team_name": home_team,
                    "teams.season_opp.game_id": game_id
                },
                {
                    "$set": {
                        "teams.$[team].season_opp.$[game].home_score": home_score,
                        "teams.$[team].season_opp.$[game].away_score": away_score,
                        "teams.$[team].wins": update_home_wins,
                        "teams.$[team].losses": updated_home_losses,
                    }
                },
                array_filters=[
                    {"team.team_name": home_team},
                    {"game.game_id": game_id}
                ]
            )
            await self.sports_collection.find_one_and_update(
                {
                    **dataset_filter,
                    "teams.team_name": away_team,
                    "teams.season_opp.game_id": game_id
                },
                {
                    "$set": {
                        "teams.$[team].season_opp.$[game].home_score": home_score,
                        "teams.$[team].season_opp.$[game].away_score": away_score,
                        "teams.$[team].wins": updated_away_wins,
                        "teams.$[team].losses": updated_away_losses
                    }
                },
                array_filters=[
                    {"team.team_name": away_team},
                    {"game.game_id": game_id}
                ]
            )

    async def update_teams_info(
        self,
        home_team: str,
        home_score: int,
        away_team: str,
        away_score: int,
        date: str,
        game_id: str = None
    ):
        """Update a canonical game's scores and any materialized team records."""
        if home_score < 0 or away_score < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Scores cannot be negative"
            )

        dataset_query = {
            "_id": self.level_constant.get('_id'),
            "sport_type": self.level_key[0],
            "gender": self.level_key[1],
            "level": self.level_key[2]
        }
        game_dataset_query = {
            "sport_type": self.level_key[0],
            "gender": self.level_key[1],
            "level": self.level_key[2]
        }

        try:
            document = await self.sports_collection.find_one(
                dataset_query,
                {"teams": 1}
            )
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Game dataset not found"
                )

            teams = document.get("teams", [])
            normalized_home_name = home_team.strip().casefold()
            normalized_away_name = away_team.strip().casefold()
            home_team_data = next(
                (
                    team for team in teams
                    if str(team.get("team_name", "")).strip().casefold()
                    == normalized_home_name
                ),
                None
            )
            away_team_data = next(
                (
                    team for team in teams
                    if str(team.get("team_name", "")).strip().casefold()
                    == normalized_away_name
                ),
                None
            )
            if not home_team_data or not away_team_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="One or both teams were not found"
                )

            canonical_id = canonical_game_id(
                date,
                home_team_data["team_id"],
                away_team_data["team_id"],
            )
            if game_id and game_id != canonical_id:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="The selected teams and date do not match the game ID",
                )
            canonical_game = await self.games_collection.find_one({
                **game_dataset_query,
                "game_id": canonical_id,
            })
            if not canonical_game:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Game not found for the selected teams and date",
                )

            def find_game(team: Dict[str, Any], opponent_id: int):
                return next(
                    (
                        game for game in team.get("season_opp", [])
                        if game.get("opponent_id") == opponent_id
                        and game.get("game_date") == canonical_game["game_date"]
                        and game.get("game_id") == canonical_id
                    ),
                    None
                )

            home_game = find_game(home_team_data, away_team_data["team_id"])
            away_game = find_game(away_team_data, home_team_data["team_id"])
            if home_game and home_game.get("home_team") not in (1, True, "1"):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="The selected home and away teams do not match the stored game"
                )
            if away_game and away_game.get("home_team") in (1, True, "1"):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="The selected home and away teams do not match the stored game"
                )

            old_home_score = float(canonical_game.get("home_score", 0))
            old_away_score = float(canonical_game.get("away_score", 0))
            old_home_won = old_home_score > old_away_score
            new_home_won = home_score > away_score

            materialized_records = 0
            for materialized_game in (home_game, away_game):
                if materialized_game:
                    materialized_game["home_score"] = home_score
                    materialized_game["away_score"] = away_score
                    materialized_records += 1

            if materialized_records and old_home_won != new_home_won:
                if new_home_won:
                    home_team_data["wins"] = home_team_data.get("wins", 0) + 1
                    home_team_data["losses"] = max(
                        0,
                        home_team_data.get("losses", 0) - 1
                    )
                    away_team_data["wins"] = max(
                        0,
                        away_team_data.get("wins", 0) - 1
                    )
                    away_team_data["losses"] = away_team_data.get(
                        "losses", 0) + 1
                else:
                    home_team_data["wins"] = max(
                        0,
                        home_team_data.get("wins", 0) - 1
                    )
                    home_team_data["losses"] = home_team_data.get(
                        "losses", 0) + 1
                    away_team_data["wins"] = away_team_data.get("wins", 0) + 1
                    away_team_data["losses"] = max(
                        0,
                        away_team_data.get("losses", 0) - 1
                    )

            game_result = await self.games_collection.update_one(
                {"_id": canonical_game["_id"]},
                {"$set": {
                    "home_score": home_score,
                    "away_score": away_score,
                    "updated_at": datetime.now(timezone.utc),
                }},
            )
            if not game_result.matched_count:
                raise RuntimeError("Canonical game disappeared during update")
            if materialized_records:
                sports_result = await self.sports_collection.update_one(
                    dataset_query,
                    {"$set": {
                        "teams": teams,
                        "rankings_stale": True,
                    }},
                )
                if not sports_result.matched_count:
                    raise RuntimeError(
                        "Game dataset disappeared during update")

            return {
                "message": (
                    f"Updated {home_team} vs {away_team} on "
                    f"{canonical_game['game_date']}"
                ),
                "status": status.HTTP_200_OK,
                "updated": {
                    "game_id": canonical_id,
                    "canonical_games": 1,
                    "team_game_records": materialized_records,
                    "source_upload_changed": False,
                }
            }
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error"
            ) from exc

    @staticmethod
    def _decode_csv_filedata(filedata: Any) -> bytes:
        """Decode current Binary data and legacy Base64-encoded CSV data."""
        if isinstance(filedata, str):
            try:
                return base64.b64decode(filedata, validate=True)
            except (ValueError, TypeError, binascii.Error):
                return filedata.encode("utf-8")
        return bytes(filedata)

    @staticmethod
    def _rename_team_in_teams(
        teams: List[Dict[str, Any]],
        team_id: int,
        team_names: set,
        new_team_name: str
    ) -> Dict[str, int]:
        """Rename a team and opponent references in one teams array."""
        normalized_team_names = {
            name.strip().casefold() for name in team_names if name.strip()
        }
        name_pattern = re.compile(
            "|".join(
                re.escape(name)
                for name in sorted(team_names, key=len, reverse=True)
                if name.strip()
            ),
            re.IGNORECASE
        ) if normalized_team_names else None
        team_records_updated = 0
        game_records_updated = 0
        game_ids_updated = 0

        for team in teams:
            if team.get("team_id") == team_id:
                if team.get("team_name") != new_team_name:
                    team["team_name"] = new_team_name
                    team_records_updated += 1
                if team.get("short_name"):
                    team["short_name"] = new_team_name

            for game in team.get("season_opp", []):
                opponent_name = str(game.get("opponent_name", "")) \
                    .strip().casefold()
                if (
                    game.get("opponent_id") == team_id
                    or opponent_name in normalized_team_names
                ):
                    if game.get("opponent_name") != new_team_name:
                        game["opponent_name"] = new_team_name
                        game_records_updated += 1

                game_id = game.get("game_id")
                if name_pattern and isinstance(game_id, str):
                    updated_game_id = name_pattern.sub(new_team_name, game_id)
                    if updated_game_id != game_id:
                        game["game_id"] = updated_game_id
                        game_ids_updated += 1

        return {
            "team_records": team_records_updated,
            "game_records": game_records_updated,
            "game_ids": game_ids_updated
        }

    @staticmethod
    def _collect_team_names(
        teams: List[Dict[str, Any]],
        team_id: int
    ) -> set:
        """Collect current and stale aliases tied to a stable team ID."""
        names = set()
        for team in teams:
            if team.get("team_id") == team_id:
                names.update(
                    str(team[field]).strip()
                    for field in ("team_name", "short_name", "long_name")
                    if team.get(field)
                )
            for game in team.get("season_opp", []):
                if game.get("opponent_id") == team_id \
                        and game.get("opponent_name"):
                    names.add(str(game["opponent_name"]).strip())
        return {name for name in names if name}

    @staticmethod
    def _rename_team_in_flagged_games(
        flagged_games: List[Dict[str, Any]],
        team_id: int,
        team_names: set,
        new_team_name: str
    ) -> Dict[str, int]:
        """Rename both possible team fields in flagged game records."""
        normalized_team_names = {
            name.strip().casefold() for name in team_names if name.strip()
        }
        name_pattern = re.compile(
            "|".join(
                re.escape(name)
                for name in sorted(team_names, key=len, reverse=True)
                if name.strip()
            ),
            re.IGNORECASE
        ) if normalized_team_names else None
        name_replacements = 0
        game_ids_updated = 0

        for game in flagged_games:
            for position in (1, 2):
                id_key = f"team{position}_id"
                name_key = f"team{position}_name"
                stored_name = str(game.get(name_key, "")).strip().casefold()
                if (
                    game.get(id_key) == team_id
                    or stored_name in normalized_team_names
                ) and game.get(name_key) != new_team_name:
                    game[name_key] = new_team_name
                    name_replacements += 1

            game_id = game.get("game_id")
            if name_pattern and isinstance(game_id, str):
                updated_game_id = name_pattern.sub(new_team_name, game_id)
                if updated_game_id != game_id:
                    game["game_id"] = updated_game_id
                    game_ids_updated += 1

        return {
            "team_names": name_replacements,
            "game_ids": game_ids_updated
        }

    async def update_team_name(
        self,
        team_id: int,
        new_team_name: str
    ):
        new_team_name = new_team_name.strip()
        if not new_team_name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="New team name cannot be empty"
            )

        dataset_query = {
            "_id": self.level_constant.get('_id'),
            "sport_type": self.level_key[0],
            "gender": self.level_key[1],
            "level": self.level_key[2]
        }
        related_query = {
            "sport_type": self.level_key[0],
            "gender": self.level_key[1],
            "level": self.level_key[2]
        }

        try:
            current_document = await self.sports_collection.find_one(
                dataset_query,
                {"teams": 1}
            )
            if not current_document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Team not found"
                )

            current_teams = current_document.get("teams", [])
            selected_team = next(
                (
                    team for team in current_teams
                    if team.get("team_id") == team_id
                ),
                None
            )
            if not selected_team:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Team not found"
                )

            old_team_name = selected_team.get("team_name", "").strip()
            if old_team_name == new_team_name:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="New team name must be different from the current name"
                )

            normalized_new_name = new_team_name.casefold()
            duplicate_team = next(
                (
                    team for team in current_teams
                    if team.get("team_id") != team_id
                    and normalized_new_name in {
                        normalize_team_name(team.get(field) or "").casefold()
                        for field in ("team_name", "short_name", "long_name")
                        if team.get(field)
                    }
                ),
                None
            )
            if duplicate_team:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"A team named {new_team_name} already exists"
                )

            flagged_document = await self.flagged_games.find_one(related_query)
            flagged_entries = flagged_document.get("flagged_games", []) \
                if flagged_document else []
            archived_document = await self.previous_season.find_one(
                dataset_query,
                {"teams": 1}
            )
            archived_teams = archived_document.get("teams", []) \
                if archived_document else []

            known_team_names = self._collect_team_names(
                current_teams,
                team_id
            )
            known_team_names.update(self._collect_team_names(
                archived_teams,
                team_id
            ))
            for flagged_game in flagged_entries:
                for position in (1, 2):
                    if flagged_game.get(f"team{position}_id") == team_id:
                        stored_name = flagged_game.get(f"team{position}_name")
                        if stored_name:
                            known_team_names.add(str(stored_name).strip())
            known_team_names.add(old_team_name)

            current_stats = self._rename_team_in_teams(
                current_teams,
                team_id,
                known_team_names,
                new_team_name
            )

            flagged_stats = self._rename_team_in_flagged_games(
                flagged_entries,
                team_id,
                known_team_names,
                new_team_name
            )

            archived_stats = {
                "team_records": 0,
                "game_records": 0,
                "game_ids": 0
            }
            if archived_document:
                archived_stats = self._rename_team_in_teams(
                    archived_teams,
                    team_id,
                    known_team_names,
                    new_team_name
                )

            current_result = await self.sports_collection.update_one(
                dataset_query,
                {"$set": {"teams": current_teams}}
            )
            if not current_result.matched_count:
                raise RuntimeError("Team dataset disappeared during update")

            now = datetime.now(timezone.utc)
            home_games_result = await self.games_collection.update_many(
                {**related_query, "home_team_id": team_id},
                {"$set": {
                    "home_team": new_team_name,
                    "updated_at": now,
                }},
            )
            away_games_result = await self.games_collection.update_many(
                {**related_query, "away_team_id": team_id},
                {"$set": {
                    "away_team": new_team_name,
                    "updated_at": now,
                }},
            )
            if flagged_document and any(flagged_stats.values()):
                await self.flagged_games.update_one(
                    {"_id": flagged_document["_id"]},
                    {"$set": {"flagged_games": flagged_entries}}
                )
            if archived_document and (
                archived_stats["team_records"]
                or archived_stats["game_records"]
                or archived_stats["game_ids"]
            ):
                await self.previous_season.update_one(
                    {"_id": archived_document["_id"]},
                    {"$set": {"teams": archived_teams}}
                )

            return {
                "message": f"{old_team_name} was renamed to {new_team_name}",
                "status": status.HTTP_200_OK,
                "updated": {
                    "team_records": current_stats["team_records"],
                    "game_records": current_stats["game_records"],
                    "game_ids": current_stats["game_ids"],
                    "canonical_games": (
                        home_games_result.modified_count
                        + away_games_result.modified_count
                    ),
                    "source_uploads_changed": 0,
                    "flagged_games": flagged_stats["team_names"],
                    "flagged_game_ids": flagged_stats["game_ids"],
                    "archived_team_records": archived_stats["team_records"],
                    "archived_game_records": archived_stats["game_records"],
                    "archived_game_ids": archived_stats["game_ids"]
                }
            }
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error"
            ) from exc

    async def update_team_info(
        self,
        team_id: int,
        team_info: Dict[str, Any],
    ):
        """Update editable team metadata and propagate a changed short name."""
        team_info = {
            "short_name": normalize_team_name(team_info.get("short_name", "")),
            "long_name": normalize_team_name(team_info.get("long_name", "")),
            "state": normalize_team_name(team_info.get("state", "")),
            "division": normalize_team_name(team_info.get("division", "")),
            "conference": normalize_team_name(team_info.get("conference", "")),
            "ranked": bool(team_info.get("ranked", False)),
        }
        if not team_info["short_name"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Short team name cannot be empty",
            )

        dataset_query = {
            "_id": self.level_constant.get("_id"),
            "sport_type": self.level_key[0],
            "gender": self.level_key[1],
            "level": self.level_key[2],
        }
        document = await self.sports_collection.find_one(dataset_query, {"teams": 1})
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found",
            )

        teams = document.get("teams", [])
        selected_team = next(
            (team for team in teams if team.get("team_id") == team_id),
            None,
        )
        if not selected_team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found",
            )

        updated_aliases = {
            value.casefold()
            for value in (team_info["short_name"], team_info["long_name"])
            if value
        }
        for team in teams:
            if team.get("team_id") == team_id:
                continue
            existing_aliases = {
                normalize_team_name(team.get(field) or "").casefold()
                for field in ("team_name", "short_name", "long_name")
                if team.get(field)
            }
            if updated_aliases.intersection(existing_aliases):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A team with this short or long name already exists",
                )

        current_team_name = selected_team.get("team_name", "")
        if current_team_name != team_info["short_name"]:
            await self.update_team_name(team_id, team_info["short_name"])
            document = await self.sports_collection.find_one(dataset_query, {"teams": 1})
            teams = document.get("teams", []) if document else []
            selected_team = next(
                (team for team in teams if team.get("team_id") == team_id),
                None,
            )
            if not selected_team:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Team not found",
                )

        selected_team.update(team_info)
        selected_team["team_name"] = team_info["short_name"]
        result = await self.sports_collection.update_one(
            dataset_query,
            {"$set": {"teams": teams}},
        )
        if not result.matched_count:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found",
            )

        return {
            "status": status.HTTP_200_OK,
            "message": f"Updated {team_info['short_name']} information",
            "team": team_info,
        }

    def _season_reset_pipeline(self, match_query=None):
        pipeline = []
        if match_query is not None:
            pipeline.append({"$match": match_query})

        pipeline.extend([
            {"$addFields": {
                "teams": {
                    "$map": {
                        "input": "$teams",
                        "as": "team",
                        "in": {
                            "$mergeObjects": [
                                "$$team",
                                {
                                    "win_ratio": 0.0,
                                    "wins": 0,
                                    "losses": 0,
                                    "season_initial_power": {
                                        "$cond": [
                                            {"$isArray": "$$team.power_ranking"},
                                            {"$cond": [
                                                {"$gt": [
                                                    {"$size": "$$team.power_ranking"},
                                                    0
                                                ]},
                                                {"$arrayElemAt": [
                                                    "$$team.power_ranking",
                                                    -1
                                                ]},
                                                None
                                            ]},
                                            None
                                        ]
                                    },
                                    "season_opp": {
                                        "$cond": [
                                            {"$isArray": "$$team.season_opp"},
                                            {"$slice": [
                                                "$$team.season_opp", -5]},
                                            []
                                        ]
                                    }
                                }
                            ]
                        }
                    }
                }
            }},
            {"$merge": {
                "into": self.sports_collection.name,
                "on": "_id",
                "whenMatched": "replace"
            }}
        ])
        return pipeline

    async def _reset_seasons(self, match_query=None):
        reset_cursor = self.sports_collection.aggregate(
            self._season_reset_pipeline(match_query)
        )
        await reset_cursor.to_list(None)

    async def _delete_current_games(self, dataset_query=None):
        """Delete canonical games, upload metadata, and their source files."""
        dataset_query = dataset_query or {}
        upload_documents = await self.csv_collection.find(
            dataset_query,
            {"csv_files.storage_path": 1},
        ).to_list(length=None)
        files_deleted = 0
        for document in upload_documents:
            for upload in document.get("csv_files", []):
                storage_path = upload.get("storage_path")
                if storage_path and delete_game_file(storage_path):
                    files_deleted += 1
        games_result = await self.games_collection.delete_many(dataset_query)
        uploads_result = await self.csv_collection.delete_many(dataset_query)
        return {
            "games_deleted": games_result.deleted_count,
            "upload_records_deleted": uploads_result.deleted_count,
            "upload_files_deleted": files_deleted,
        }

    async def clear_season(self):
        """Reset the selected season without modifying archive storage."""

        dataset_query = {
            "sport_type": self.level_key[0],
            "gender": self.level_key[1],
            "level": self.level_key[2],
        }
        deleted = await self._delete_current_games(dataset_query)
        await self._reset_seasons({
            "_id": self.level_constant.get("_id")
        })

        doc = await self.sports_collection.find_one({"_id": self.level_constant.get("_id")})

        return {
            "archive_unchanged": True,
            "teams_reset": doc is not None,
            **deleted,
            "return_data": (
                "Reset selected sport"
                if doc is not None
                else "Failed to reset selected sport"
            ),
        }

    async def reset_all_sports(self):
        """Reset every current sport dataset without modifying archive storage."""

        deleted = await self._delete_current_games()
        await self._reset_seasons()
        datasets_reset = await self.sports_collection.count_documents({})

        return {
            "archive_unchanged": True,
            "datasets_reset": datasets_reset,
            **deleted,
            "return_data": f"Reset {datasets_reset} sports datasets",
        }

    async def get_team_names_and_ids(self):
        query: Dict = query_params_builder()
        query.update(
            _id=self.level_constant.get('_id'),
            sport_type=self.level_key[0],
            gender=self.level_key[1],
            level=self.level_key[2]
        )

        projection = {
            "teams.team_name": 1,
            "teams.team_id": 1,
            "teams.short_name": 1,
            "teams.long_name": 1,
            "teams.state": 1,
            "teams.division": 1,
            "teams.conference": 1,
            "teams.ranked": 1,
            "_id": 0,
        }

        try:
            cursor = self.sports_collection.find(query, projection)
            documents = await cursor.to_list(length=None)

            teams = [
                {
                    "team_name": team["team_name"],
                    "team_id": team["team_id"],
                    "short_name": team.get("short_name", team["team_name"]),
                    "long_name": team.get("long_name", ""),
                    "state": team.get("state", ""),
                    "division": team.get("division", ""),
                    "conference": team.get("conference", ""),
                    "ranked": team.get("ranked", False),
                }
                for doc in documents if "teams" in doc
                for team in doc["teams"]
            ]

            if teams:
                return {
                    "message": "Successfully Found Teams",
                    "status": status.HTTP_200_OK,
                    "data": {"teams": teams}
                }
            return {
                "message": "Did Not Find Any Teams",
                "status": status.HTTP_204_NO_CONTENT,
                "data": None
            }
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error"
            ) from exc

    async def get_all_teams(self) -> List[Dict[str, Any]]:
        """Return every stored field for teams in the selected dataset."""
        document = await self.sports_collection.find_one(
            {"_id": self.level_constant.get("_id")},
            {"teams": 1, "_id": 0},
        )
        return document.get("teams", []) if document else []

    async def find_season_opp_dates(
        self,
        team_one: int,
        team_two: int
    ):
        """Return active canonical games between two teams.

        Team documents can retain a five-game historical snapshot after a
        season reset. Those records are read-only and must not appear in the
        update/delete game workflows.
        """
        query = {
            "sport_type": self.level_key[0],
            "gender": self.level_key[1],
            "level": self.level_key[2],
            "$or": [
                {
                    "home_team_id": team_one,
                    "away_team_id": team_two,
                },
                {
                    "home_team_id": team_two,
                    "away_team_id": team_one,
                },
            ],
        }
        projection = {
            "_id": 0,
            "game_date": 1,
            "game_id": 1,
            "home_team_id": 1,
            "home_team": 1,
            "away_team_id": 1,
            "away_team": 1,
            "home_score": 1,
            "away_score": 1,
        }
        cursor = self.games_collection.find(
            query,
            projection,
        ).sort([
            ("game_date", 1),
            ("game_id", 1),
        ])
        games = await cursor.to_list(length=None)

        return [
            {
                "game_date": game.get("game_date"),
                "game_id": game.get("game_id"),
                "home_team_id": game.get("home_team_id"),
                "home_team_name": game.get("home_team"),
                "away_team_id": game.get("away_team_id"),
                "away_team_name": game.get("away_team"),
                "home_score": game.get("home_score"),
                "away_score": game.get("away_score"),
            }
            for game in games
        ]

    async def delete_game(
        self,
        team_one: int,
        team_two: int,
        game_id: str,
        game_date: str
    ):
        dataset_query = {
            "sport_type": self.level_key[0],
            "gender": self.level_key[1],
            "level": self.level_key[2],
        }
        try:
            canonical_game = await self.games_collection.find_one({
                **dataset_query,
                "game_id": game_id,
                "game_date": normalized_date(game_date),
                "home_team_id": team_one,
                "away_team_id": team_two,
            })
            if not canonical_game:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Game not found",
                )

            current_document = await self.sports_collection.find_one(
                {"_id": self.level_constant.get("_id")},
                {"teams": 1},
            )
            teams = current_document.get("teams", []) \
                if current_document else []
            home_won = (
                canonical_game["home_score"] > canonical_game["away_score"]
            )
            team_records_removed = 0
            for team in teams:
                if team.get("team_id") not in (team_one, team_two):
                    continue
                games_before = team.get("season_opp", [])
                team["season_opp"] = [
                    game for game in games_before
                    if game.get("game_id") != game_id
                ]
                if len(team["season_opp"]) == len(games_before):
                    continue
                team_records_removed += 1
                won = home_won if team["team_id"] == team_one else not home_won
                record_key = "wins" if won else "losses"
                team[record_key] = max(0, int(team.get(record_key, 0)) - 1)
                total = int(team.get("wins", 0)) + int(team.get("losses", 0))
                team["win_ratio"] = (
                    int(team.get("wins", 0)) / total if total else 0.0
                )

            delete_result = await self.games_collection.delete_one({
                "_id": canonical_game["_id"],
            })
            if current_document:
                await self.sports_collection.update_one(
                    {"_id": self.level_constant.get("_id")},
                    {"$set": {
                        "teams": teams,
                        "rankings_stale": True,
                    }},
                )

            return {
                "message": "Game was successfully removed",
                "deleted": {
                    "canonical_games": delete_result.deleted_count,
                    "team_game_records": team_records_removed,
                    "source_uploads_changed": 0,
                },
                "status": status.HTTP_200_OK,
            }
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error"
            ) from exc

    @staticmethod
    def _remove_team_from_teams(
        teams: List[Dict[str, Any]],
        team_id: int,
        team_name: str
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Remove a team and every reciprocal game reference from a dataset."""
        selected_team = next(
            (
                team for team in teams
                if team.get("team_id") == team_id
                and team.get("team_name") == team_name
            ),
            None
        )
        selected_games = selected_team.get("season_opp", []) \
            if selected_team else []
        selected_game_ids = {
            game.get("game_id") for game in selected_games
            if game.get("game_id")
        }
        normalized_name = team_name.strip().casefold()
        linked_games_removed = 0
        remaining_teams = []

        for current_team in teams:
            if current_team is selected_team:
                continue

            remaining_games = []
            for game in current_team.get("season_opp", []):
                opponent_name = str(game.get("opponent_name", "")) \
                    .strip().casefold()
                is_related = (
                    game.get("opponent_id") == team_id
                    or opponent_name == normalized_name
                    or game.get("game_id") in selected_game_ids
                )
                if not is_related:
                    remaining_games.append(game)
                    continue

                linked_games_removed += 1
                try:
                    home_score = float(game.get("home_score"))
                    away_score = float(game.get("away_score"))
                    is_home = game.get("home_team") in (1, True, "1")
                    won = home_score > away_score if is_home \
                        else away_score >= home_score
                    record_key = "wins" if won else "losses"
                    current_record = int(current_team.get(record_key, 0))
                    current_team[record_key] = max(0, current_record - 1)
                except (TypeError, ValueError):
                    # The game is still removed if an older record has bad scores.
                    pass

            current_team["season_opp"] = remaining_games
            if isinstance(current_team.get("recent_opp"), list):
                current_team["recent_opp"] = [
                    0 if opponent_id == team_id else opponent_id
                    for opponent_id in current_team["recent_opp"]
                ]
            remaining_teams.append(current_team)

        return remaining_teams, {
            "team_found": selected_team is not None,
            "team_games_removed": len(selected_games),
            "linked_games_removed": linked_games_removed
        }

    async def delete_team(
        self,
        team_name: str,
        team_id: int
    ):
        dataset_query = {
            "_id": self.level_constant.get('_id'),
            "sport_type": self.level_key[0],
            "gender": self.level_key[1],
            "level": self.level_key[2]
        }
        related_query = {
            "sport_type": self.level_key[0],
            "gender": self.level_key[1],
            "level": self.level_key[2]
        }

        try:
            current_document = await self.sports_collection.find_one(
                dataset_query,
                {"teams": 1}
            )
            if not current_document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Team not found"
                )

            current_teams, current_stats = self._remove_team_from_teams(
                current_document.get("teams", []),
                team_id,
                team_name
            )
            if not current_stats["team_found"]:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Team not found"
                )

            flagged_document = await self.flagged_games.find_one(related_query)
            flagged_entries = flagged_document.get("flagged_games", []) \
                if flagged_document else []
            normalized_name = team_name.strip().casefold()

            def is_team_flag(flagged_game: Dict[str, Any]) -> bool:
                return (
                    flagged_game.get("team1_id") == team_id
                    or flagged_game.get("team2_id") == team_id
                    or str(flagged_game.get("team1_name", ""))
                    .strip().casefold() == normalized_name
                    or str(flagged_game.get("team2_name", ""))
                    .strip().casefold() == normalized_name
                )

            remaining_flags = [
                game for game in flagged_entries if not is_team_flag(game)
            ]
            flagged_games_removed = len(flagged_entries) - len(remaining_flags)

            archived_document = await self.previous_season.find_one(
                dataset_query,
                {"teams": 1}
            )
            archived_stats = {
                "team_found": False,
                "team_games_removed": 0,
                "linked_games_removed": 0
            }
            archived_teams = []
            if archived_document:
                archived_teams, archived_stats = \
                    self._remove_team_from_teams(
                        archived_document.get("teams", []),
                        team_id,
                        team_name
                    )

            current_result = await self.sports_collection.update_one(
                dataset_query,
                {"$set": {
                    "teams": current_teams,
                    "rankings_stale": True,
                }}
            )
            if not current_result.matched_count:
                raise RuntimeError("Team dataset disappeared during deletion")

            games_result = await self.games_collection.delete_many({
                **related_query,
                "$or": [
                    {"home_team_id": team_id},
                    {"away_team_id": team_id},
                ],
            })
            if flagged_document and flagged_games_removed:
                await self.flagged_games.update_one(
                    {"_id": flagged_document["_id"]},
                    {"$set": {"flagged_games": remaining_flags}}
                )
            if archived_document and (
                archived_stats["team_found"]
                or archived_stats["linked_games_removed"]
            ):
                await self.previous_season.update_one(
                    {"_id": archived_document["_id"]},
                    {"$set": {"teams": archived_teams}}
                )

            return {
                "message": f"{team_name} and related game data were deleted",
                "status": status.HTTP_200_OK,
                "deleted": {
                    "team_id": team_id,
                    "team_name": team_name,
                    "games": current_stats["team_games_removed"],
                    "linked_game_records": current_stats["linked_games_removed"],
                    "canonical_games": games_result.deleted_count,
                    "source_uploads_changed": 0,
                    "flagged_games": flagged_games_removed,
                    "archived_team": archived_stats["team_found"]
                }
            }
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error"
            ) from exc

    async def store_flagged_games(
        self,
        game_id: str,
        team1_id: int,
        team1_name: str,
        team2_id: int,
        team2_name: str
    ):
        query = {
            "sport_type": self.level_key[0],
            "gender": self.level_key[1],
            "level": self.level_key[2]
        }
        response = await self.flagged_games.update_one(
            query,
            {"$push": {"flagged_games": {
                'game_id': game_id,
                'team1_id': team1_id,
                'team1_name': team1_name,
                'team2_id': team2_id,
                'team2_name': team2_name
            }}}
        )
        return {
            'message': "Team was successfully reported" if response.modified_count else "Error marking game",
            "game_flagged": 1 if response.modified_count else 0,
            "status": 200   # Need to update this
        }

    async def clear_flagged_games(self):
        query = {
            "sport_type": self.level_key[0],
            "gender": self.level_key[1],
            "level": self.level_key[2]
        }

        response = await self.flagged_games.update_one(
            query,
            {"$set": {"flagged_games": []}}
        )

        return {
            'message': "Flagged games have been removed" if response.modified_count else "There were not games to remove",
            "status": 200
        }

    async def retrieve_flagged_games(self):
        query = {
            "sport_type": self.level_key[0],
            "gender": self.level_key[1],
            "level": self.level_key[2]
        }
        response = await self.flagged_games.find_one(
            query,
            {"_id": 0, "flagged_games": 1}
        )

        return response

    async def check_flagged_games(
        self,
        game_id: str
    ):
        print(game_id)
        query = {
            "sport_type": self.level_key[0],
            "gender": self.level_key[1],
            "level": self.level_key[2],
            "flagged_games.game_id": game_id
        }
        response = await self.flagged_games.find_one(
            query
        )
        return {
            "message": "Game has already been flagged and will be updated soon" if response else "Adding game",
            "game_flagged": 1 if response else 0,
            "status": 200
        }

    async def _add_upload_metadata(
        self,
        query: dict,
        upload_id: str,
        filename: str,
        storage_path: str,
        game_count: int,
        date: str,
        uploaded_at: datetime | None = None,
    ) -> int:
        """Store upload metadata without storing file contents in MongoDB."""
        file_entry = {
            "upload_id": upload_id,
            "filename": filename,
            "storage_path": storage_path,
            "upload_date": uploaded_at or datetime.now(timezone.utc),
            "sports_week": date,
            "game_count": game_count,
        }
        results = await self.csv_collection.update_one(
            query,
            {"$push": {"csv_files": file_entry}},
            upsert=True,
        )
        return 1 if results.modified_count or results.upserted_id else 0

    async def retrieve_games(self) -> List[Dict[str, Any]]:
        """Return canonical games for this dataset in deterministic order."""
        cursor = self.games_collection.find(
            {
                "sport_type": self.level_key[0],
                "gender": self.level_key[1],
                "level": self.level_key[2],
            },
            {"_id": 0},
        ).sort([("game_date", 1), ("game_id", 1)])
        return await cursor.to_list(length=None)

    async def migrate_legacy_uploads(self) -> Dict[str, int]:
        """Move legacy Mongo CSV blobs to disk and create canonical games."""
        dataset_query = {
            "sport_type": self.level_key[0],
            "gender": self.level_key[1],
            "level": self.level_key[2],
        }
        upload_document = await self.csv_collection.find_one(
            dataset_query,
            {"csv_files": 1},
        )
        if not upload_document:
            return {"files_migrated": 0, "games_migrated": 0}

        entries = upload_document.get("csv_files", [])
        if not any("filedata" in entry for entry in entries):
            return {"files_migrated": 0, "games_migrated": 0}

        migrated_entries = []
        files_migrated = 0
        games_migrated = 0
        files_skipped = 0
        for index, entry in enumerate(entries):
            if "filedata" not in entry:
                migrated_entries.append(entry)
                continue

            content = self._decode_csv_filedata(entry["filedata"])
            games = parse_game_csv(content)
            team_names = [
                team_name
                for game in games
                for team_name in (game.home_team, game.away_team)
            ]
            missing_teams = await self.find_missing_teams(team_names)
            if missing_teams:
                migrated_entries.append(entry)
                files_skipped += 1
                continue

            upload_id = entry.get("upload_id") or (
                f"legacy-{upload_document['_id']}-{index}"
            )
            filename = entry.get("filename") or f"legacy-{index}.csv"
            normalized_content = serialize_game_rows(games)
            _, storage_path = store_game_file(
                self.level_key,
                filename,
                normalized_content,
                upload_id=upload_id,
            )
            now = datetime.now(timezone.utc)
            game_documents = await self._build_game_documents(
                games,
                dataset_query,
            )
            operations = []
            for document in game_documents:
                document.update({
                    "source_upload_id": upload_id,
                    "source_filename": filename,
                    "created_at": now,
                    "updated_at": now,
                })
                operations.append(UpdateOne(
                    {**dataset_query, "identity": document["identity"]},
                    {"$setOnInsert": document},
                    upsert=True,
                ))
            if operations:
                result = await self.games_collection.bulk_write(
                    operations,
                    ordered=False,
                )
                games_migrated += result.upserted_count

            migrated_entries.append({
                "upload_id": upload_id,
                "filename": filename,
                "storage_path": storage_path,
                "upload_date": entry.get("upload_date", now),
                "sports_week": normalized_date(
                    entry.get("sports_week") or games[0].date
                ),
                "game_count": len(games),
                "migrated_at": now,
            })
            files_migrated += 1

        await self.csv_collection.update_one(
            {"_id": upload_document["_id"]},
            {"$set": {"csv_files": migrated_entries}},
        )
        return {
            "files_migrated": files_migrated,
            "games_migrated": games_migrated,
            "files_skipped_unknown_teams": files_skipped,
        }

    async def _find_teams(self, query: dict, teams_search: list) -> list:
        """Finds the teams that are in the database and
        returns those for filtering which teams are not
        in the database

        Args:
            query (dict): Filtering query for db
            teams_search (list): list of teams to search for

        Returns:
            list: returns the list of teams that were found (if
            any)
        """
        results = self.sports_collection.find(
            {**query, "teams": {"$nin": teams_search}},
            {"_id": 0}
        )
        return await results.to_list()
