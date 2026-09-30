"""Logical operations for Admin
"""


import os
import io
import asyncio
import binascii
import re
from io import StringIO
from typing import Any, List, Dict, Tuple
import traceback
import csv
import pandas as pd
import base64
from datetime import datetime
from fastapi import HTTPException, status, UploadFile
import bson
from bson.binary import Binary
import motor.motor_asyncio
from api.config.constants import LEVEL_CONSTANTS
from api.utils.json_helper import query_params_builder


MONGO_DETAILS = os.getenv("MONGO_URI") or \
    f"mongodb+srv://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASS')}@" \
    "sports-cluster.mx1mo.mongodb.net/" \
    "?retryWrites=true&w=majority&appName=Sports-Cluster"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
database = client["sports_data"]


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
        self.flagged_games = database.get_collection('flagged_games')
        self.previous_season = database.get_collection('previous_season')
        self.level_key = level_key
        self.level_constant = LEVEL_CONSTANTS[level_key]
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
            dict: Message for successful upload and an array of missing teams (if any).
        """
        try:
            # Read the uploaded CSV file
            file_name = csv_file.filename
            file_content = await csv_file.read()
            decode_content = file_content.decode("utf-8")
            csv_reader = csv.reader(StringIO(decode_content))
            first_row = next(csv_reader, None)
            date = first_row[0]

            query_csv = {
                "sport_type": sport_type,
                "gender": gender,
                "level": level
            }

            # Add CSV file metadata to storage (this should be after validation)
            file_upload = await self._add_csv_file(
                query_csv,
                file_name,
                file_content,
                date
            )
            if file_upload > 0:
                return {
                    "message": "File has been uploaded successfully",
                    "status": status.HTTP_200_OK,
                    "files_uploaded": file_upload
                }
            else:
                return {
                    "message": "No file was uploaded",
                    "status": status.HTTP_200_OK,
                    "files_uploaded": file_upload
                }

        except Exception as exc:
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An internal error has occurred."
            ) from exc

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
            documents = await self.sports_collection.find(query_base, {"teams.team_name": 1}).to_list(length=None)
            found_team_names = {
                team["team_name"] for doc in documents for team in doc["teams"] if "team_name" in team}

            missing_teams = list(set(teams) - found_team_names)
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
        added, skipped = [], []
        team_id = await self._generate_team_id()
        for team in teams:
            team_id = team_id + 1
            team_name = team.get("team_name")
            existing = await self.sports_collection.find_one(
                {**base_filter, "teams.team_name": team_name}
            )
            if existing:
                skipped.append(team_name)
                continue
            new_team_data = {
                "team_id": team_id,
                "team_name": team_name,
                "city": "",
                "state": team.get('state'),
                "division": team.get('division'),
                "conference": team.get('conference'),
                "division_rank": 0,
                "overall_rank": 0,
                "power_ranking": [{"initial": team.get('power_ranking')}],
                "win_ratio": 0.0,
                "wins": 0,
                "losses": 0,
                "date": "",
                "recent_opp": [0, 0, 0, 0, 0],
                "season_opp": []
            }
            result = await self.sports_collection.update_one(
                base_filter,
                {"$push": {"teams": new_team_data}}
            )
            if result.modified_count > 0:
                added.append(team_name)
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
        home_team_data = await self.sports_collection.find_one(
            {"teams.team_name": home_team, "teams.season_opp.game_id": game_id},
            {"teams.$": 1}
        )

        away_team_data = await self.sports_collection.find_one(
            {"teams.team_name": away_team, "teams.season_opp.game_id": game_id},
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
        """Update a game's scores in team records and its source CSV row."""
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
        related_query = {
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

            def find_game(team: Dict[str, Any], opponent_id: int):
                return next(
                    (
                        game for game in team.get("season_opp", [])
                        if game.get("opponent_id") == opponent_id
                        and game.get("game_date") == date
                        and (not game_id or game.get("game_id") == game_id)
                    ),
                    None
                )

            home_game = find_game(home_team_data, away_team_data["team_id"])
            away_game = find_game(away_team_data, home_team_data["team_id"])
            if not home_game or not away_game:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Game not found for the selected teams and date"
                )

            home_is_home = home_game.get("home_team") in (1, True, "1")
            away_is_home = away_game.get("home_team") in (1, True, "1")
            if not home_is_home or away_is_home:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="The selected home and away teams do not match the stored game"
                )

            old_home_score = float(home_game.get("home_score", 0))
            old_away_score = float(home_game.get("away_score", 0))
            old_home_won = old_home_score > old_away_score
            new_home_won = home_score > away_score

            home_game["home_score"] = home_score
            home_game["away_score"] = away_score
            away_game["home_score"] = home_score
            away_game["away_score"] = away_score

            if old_home_won != new_home_won:
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
                    away_team_data["losses"] = away_team_data.get("losses", 0) + 1
                else:
                    home_team_data["wins"] = max(
                        0,
                        home_team_data.get("wins", 0) - 1
                    )
                    home_team_data["losses"] = home_team_data.get("losses", 0) + 1
                    away_team_data["wins"] = away_team_data.get("wins", 0) + 1
                    away_team_data["losses"] = max(
                        0,
                        away_team_data.get("losses", 0) - 1
                    )

            csv_document = await self.csv_collection.find_one(related_query)
            if not csv_document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Source game file not found"
                )

            updated_csv_files = []
            csv_rows_updated = 0
            for csv_file in csv_document.get("csv_files", []):
                updated_csv_file = dict(csv_file)
                rows = list(csv.reader(StringIO(
                    self._decode_csv_filedata(
                        csv_file.get("filedata", b"")
                    ).decode("utf-8")
                )))
                file_changed = False
                for row in rows:
                    if (
                        len(row) >= 5
                        and row[0].strip() == date
                        and row[1].strip().casefold() == normalized_home_name
                        and row[2].strip().casefold() == normalized_away_name
                    ):
                        row[3] = str(home_score)
                        row[4] = str(away_score)
                        csv_rows_updated += 1
                        file_changed = True

                if file_changed:
                    output = StringIO(newline="")
                    csv.writer(output).writerows(rows)
                    updated_csv_file["filedata"] = Binary(
                        output.getvalue().encode("utf-8")
                    )
                updated_csv_files.append(updated_csv_file)

            if not csv_rows_updated:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Game row not found in uploaded files"
                )

            sports_result = await self.sports_collection.update_one(
                dataset_query,
                {"$set": {"teams": teams}}
            )
            if not sports_result.matched_count:
                raise RuntimeError("Game dataset disappeared during update")
            await self.csv_collection.update_one(
                {"_id": csv_document["_id"]},
                {"$set": {"csv_files": updated_csv_files}}
            )

            return {
                "message": f"Updated {home_team} vs {away_team} on {date}",
                "status": status.HTTP_200_OK,
                "updated": {
                    "game_id": home_game.get("game_id"),
                    "team_game_records": 2,
                    "csv_rows": csv_rows_updated
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
            if team.get("team_id") == team_id and team.get("team_name"):
                names.add(str(team["team_name"]).strip())
            for game in team.get("season_opp", []):
                if game.get("opponent_id") == team_id \
                        and game.get("opponent_name"):
                    names.add(str(game["opponent_name"]).strip())
        return {name for name in names if name}

    @classmethod
    def _rename_team_rows_in_csv(
        cls,
        filedata: Any,
        team_names: set,
        new_team_name: str
    ) -> Tuple[Binary, int]:
        """Rename either participant column in an uploaded game CSV."""
        rows = list(csv.reader(StringIO(
            cls._decode_csv_filedata(filedata).decode("utf-8")
        )))
        normalized_team_names = {
            name.strip().casefold() for name in team_names if name.strip()
        }
        replacements = 0

        for row in rows:
            for column in (1, 2):
                if (
                    len(row) > column
                    and row[column].strip().casefold() in normalized_team_names
                ):
                    row[column] = new_team_name
                    replacements += 1

        output = StringIO(newline="")
        csv.writer(output).writerows(rows)
        return Binary(output.getvalue().encode("utf-8")), replacements

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
                    and str(team.get("team_name", "")).strip().casefold()
                    == normalized_new_name
                ),
                None
            )
            if duplicate_team:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"A team named {new_team_name} already exists"
                )

            csv_document = await self.csv_collection.find_one(related_query)
            csv_files = csv_document.get("csv_files", []) \
                if csv_document else []
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

            csv_files_updated = 0
            csv_replacements = 0
            updated_csv_files = []
            for csv_file in csv_files:
                updated_csv_file = dict(csv_file)
                updated_filedata, replacements = \
                    self._rename_team_rows_in_csv(
                        csv_file.get("filedata", b""),
                        known_team_names,
                        new_team_name
                    )
                if replacements:
                    updated_csv_file["filedata"] = updated_filedata
                    csv_files_updated += 1
                    csv_replacements += replacements
                updated_csv_files.append(updated_csv_file)

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

            if csv_document and csv_files_updated:
                await self.csv_collection.update_one(
                    {"_id": csv_document["_id"]},
                    {"$set": {"csv_files": updated_csv_files}}
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
                    "csv_replacements": csv_replacements,
                    "csv_files": csv_files_updated,
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

    async def clear_season(self):
        """
        Clears the season and stores the previous season in a separate collection.
        """

        query_base = {
            "_id": 1,
            "sport_type": 1,
            "gender": 1,
            "level": 1,
            "teams": 1
        }

        # Archive the current season into previous_season collection
        pipeline = [
            {"$project": query_base},
            {"$out": "previous_season"}
        ]
        cursor = self.sports_collection.aggregate(pipeline)
        await cursor.to_list(None)  # Execute the aggregation pipeline

        update_pipeline = [
            {"$match": {"_id": self.level_constant.get("_id")}},
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
                                    "season_opp": [],
                                    "power_ranking": {
                                        "$cond": [
                                            {"$isArray": "$$team.power_ranking"},
                                            {"$cond": [
                                                {"$gt": [
                                                    {"$size": "$$team.power_ranking"}, 0]},
                                                [{"$arrayElemAt": [
                                                    "$$team.power_ranking", -1]}],
                                                []
                                            ]},
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
                "into": self.sports_collection.name,  # Use the actual collection name
                "on": "_id",
                "whenMatched": "replace"
            }}
        ]

        await self.sports_collection.aggregate(update_pipeline).to_list(None)

        doc = await self.sports_collection.find_one({"_id": self.level_constant.get("_id")})

        return {
            "archived": True,
            "teams_reset": doc is not None,
            "return_data": "Cleared season" if doc is not None else "Failed to clear season",
        }

    async def get_team_names_and_ids(self):
        query: Dict = query_params_builder()
        query.update(
            _id=self.level_constant.get('_id'),
            sport_type=self.level_key[0],
            gender=self.level_key[1],
            level=self.level_key[2]
        )

        projection = {"teams.team_name": 1, "teams.team_id": 1, "_id": 0}

        try:
            cursor = self.sports_collection.find(query, projection)
            documents = await cursor.to_list(length=None)

            teams = [
                {"team_name": team["team_name"], "team_id": team["team_id"]}
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

    async def find_season_opp_dates(
        self,
        team_one: int,
        team_two: int
    ):
        query = {
            "_id": self.level_constant.get('_id'),
            "sport_type": self.level_key[0],
            "gender": self.level_key[1],
            "level": self.level_key[2],
            "teams.team_id": team_one
        }

        projection = {"teams.$": 1}

        document = await self.sports_collection.find_one(
            query,
            projection
        )

        if not document:
            return []
        result = []
        for team in document.get('teams', []):
            for game in team.get('season_opp', []):
                if game.get('opponent_id') == team_two:
                    result.append({
                        'game_date': game.get('game_date'),
                        'game_id': game.get('game_id'),
                        'home_team_id': team.get('team_id')
                        if game.get('home_team') in (1, True, "1")
                        else game.get('opponent_id'),
                        'home_team_name': team.get('team_name')
                        if game.get('home_team') in (1, True, "1")
                        else game.get('opponent_name'),
                        'away_team_id': game.get('opponent_id')
                        if game.get('home_team') in (1, True, "1")
                        else team.get('team_id'),
                        'away_team_name': game.get('opponent_name')
                        if game.get('home_team') in (1, True, "1")
                        else team.get('team_name'),
                        'home_score': game.get('home_score'),
                        'away_score': game.get('away_score')
                    })

        return result

    async def delete_game(
        self,
        team_one: int,
        team_two: int,
        game_id: str,
        game_date: str
    ):
        # Need to clear the season_opp array for both teams, utilizing team id's
        # and game id
        query1 = {
            "_id": self.level_constant.get('_id'),
            "sport_type": self.level_key[0],
            "gender": self.level_key[1],
            "level": self.level_key[2],
            "teams.team_id": team_one,
            "teams.season_opp.game_id": game_id
        }
        update = {
            "$pull": {
                "teams.$.season_opp": {
                    "game_id": game_id
                }
            }
        }

        query2 = {
            "_id": self.level_constant.get('_id'),
            "sport_type": self.level_key[0],
            "gender": self.level_key[1],
            "level": self.level_key[2],
            "teams.team_id": team_two,
            "teams.season_opp.game_id": game_id
        }

        query_csv = {
            "_id": self.level_constant.get('_id'),
            "sport_type": self.level_key[0],
            "gender": self.level_key[1],
            "level": self.level_key[2],
            "csv_files.sports_week": game_date
        }
        try:
            team_1_delete = await self.sports_collection.find_one_and_update(query1, update)
            team_2_delete = await self.sports_collection.find_one_and_update(query2, update)

            csv_file = await self.sports_collection.find_one(query_csv, {"csv_files.$": 1})

            if csv_file and "csv_files" in csv_file:
                csv_document = csv_file["csv_files"][0]

                csv_string = csv_document["filedata"].decode("utf-8")
                df = pd.read_csv(io.StringIO(csv_string), header=None)

                df_filtered = df[~df.iloc[:, 1].isin([team_one, team_two])]

                new_csv_string = df_filtered.to_csv(index=False, header=False)
                new_filedata_binary = bson.Binary(
                    new_csv_string.encode("utf-8"))

                updated_csv = await self.sports_collection.update_one(
                    query_csv,
                    {"$set": {"csv_files.$.filedata": new_filedata_binary}}
                )

            return {
                "message": "Game was successfully removed" if team_1_delete and team_2_delete else "Error removing both games",
                "csv_file": "CSV file was successfully updated" if updated_csv else "CSV file was not updated",
                "status": status.HTTP_200_OK
            }
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

    @staticmethod
    def _remove_team_rows_from_csv(
        filedata: Any,
        team_name: str
    ) -> Tuple[Binary, int]:
        """Remove rows where the selected team is either game participant."""
        raw_filedata = AdminTeamsService._decode_csv_filedata(filedata)
        rows = list(csv.reader(StringIO(raw_filedata.decode("utf-8"))))
        normalized_name = team_name.strip().casefold()

        def includes_team(row: List[str]) -> bool:
            return any(
                len(row) > column
                and row[column].strip().casefold() == normalized_name
                for column in (1, 2)
            )

        filtered_rows = [row for row in rows if not includes_team(row)]
        rows_removed = len(rows) - len(filtered_rows)
        output = StringIO(newline="")
        csv.writer(output).writerows(filtered_rows)
        return Binary(output.getvalue().encode("utf-8")), rows_removed

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

            csv_document = await self.csv_collection.find_one(related_query)
            csv_files = csv_document.get("csv_files", []) \
                if csv_document else []
            csv_rows_removed = 0
            csv_files_updated = 0
            updated_csv_files = []
            for csv_file in csv_files:
                updated_csv_file = dict(csv_file)
                updated_filedata, rows_removed = \
                    self._remove_team_rows_from_csv(
                        csv_file.get("filedata", b""),
                        team_name
                    )
                if rows_removed:
                    updated_csv_file["filedata"] = updated_filedata
                    csv_rows_removed += rows_removed
                    csv_files_updated += 1
                updated_csv_files.append(updated_csv_file)

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
                {"$set": {"teams": current_teams}}
            )
            if not current_result.matched_count:
                raise RuntimeError("Team dataset disappeared during deletion")

            if csv_document and csv_files_updated:
                await self.csv_collection.update_one(
                    {"_id": csv_document["_id"]},
                    {"$set": {"csv_files": updated_csv_files}}
                )
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
                    "csv_rows": csv_rows_removed,
                    "csv_files": csv_files_updated,
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

    async def _add_csv_file(
        self,
        query: dict,
        filename: str,
        csv_file: Any,
        date: str
    ) -> int:
        """Adds a csv file to the database for later
        processing

        Args:
            query (dict): Filtering query for db
            filename (str): CSV filename
            csv_file (Any): CSV file data

        Returns:
            int: The number of uploaded documents
        """
        file_entry = {
            "filename": filename,
            "filedata": Binary(csv_file),
            "upload_date": str(datetime.today()),
            "sports_week": date
        }
        results = await self.csv_collection.update_one(
            query,
            {"$push": {"csv_files": file_entry}},
            upsert=True
        )
        return results.modified_count

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

    async def _generate_team_id(self) -> int:
        """Gets teams and finds the max team id and then
        sets the new teams id to the max + 1

        Returns:
            int: Returns the new team id
        """
        teams = await self.sports_collection.find_one(
            {'_id': self.level_constant.get('_id')},
            projection={"teams": 1, "_id": 0}
        )
        team_list = teams.get("teams", []) if teams else []
        existing_ids = [team.get("team_id")
                        for team in team_list if "team_id" in team]
        return max(existing_ids) if existing_ids else 0

    async def retrieve_csv_file(self) -> Dict:
        """Retrieves the CSV file from the database

        Returns:
            Dict: Returns the contents received from
            MongoDB
        """
        csv_document = await self.csv_collection.find_one(
            {
                "sport_type": self.level_key[0],
                "gender": self.level_key[1],
                "level": self.level_key[2]
            },
            {"csv_files": 1}
        )
        return csv_document['csv_files']
