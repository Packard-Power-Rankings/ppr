import os
from io import StringIO
from typing import Any, List, Dict, Tuple
import traceback
import csv
from datetime import datetime
from fastapi import HTTPException, status, UploadFile
from bson.binary import Binary
import motor.motor_asyncio
from config.config import LEVEL_CONSTANTS
from schemas import items

MONGO_DETAILS = \
    f"mongodb+srv://{os.getenv("MONGO_USER")}:{os.getenv("MONGO_PASS")}@" \
    "sports-cluster.mx1mo.mongodb.net/" \
    "?retryWrites=true&w=majority&appName=Sports-Cluster"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
database = client["sports_data"]

class AdminTeamsService():
    def __init__(self, level_key: Tuple):
        self.sports_collection = database.get_collection('teams_data')
        self.csv_collection = database.get_collection('csv_files')
        self.previous_season = database.get_collection('previous_season')
        self.level_constant = LEVEL_CONSTANTS[level_key]

    async def store_csv_check_teams(
        self,
        sport_type: str,
        gender: str,
        level: str,
        csv_file: UploadFile
    ):
        """Admin level http post method

        Args:
            sport_type (str): Type Of Sport
            gender (str): Sport Gender
            level (str): Sport Level
            csv_file (UploadFile): CSV File to Store

        Raises:
            HTTPException: 400 Bad Request
            HTTPException: 404 Not Found

        Returns:
            dict: Message for succesfull upload and an array of
            missing teams (if any).
        """
        try:
            file_name = csv_file.filename
            file_content = await csv_file.read()
            query_csv = {
                "sport_type": sport_type,
                "gender": gender,
                "level": level
            }
            file_upload = await self._add_csv_file(
                query_csv,
                file_name,
                file_content
            )

            decode_content = file_content.decode("utf-8")
            csv_reader = csv.reader(StringIO(decode_content))

            team_check: List[str] = []
            for team in csv_reader:
                team_check.append(team[1].lower())
                team_check.append(team[2].lower())

            query_teams = {
                "_id": self.level_constant.get('_id')
            }
            results = await self._find_teams(query_teams, team_check)

            if results:
                teams: List[Dict[str, str]] = results[0].get('teams')
                for team in teams:
                    if team.get('team_name').lower() in \
                        [t.lower() for t in team_check]:
                            team_check = [
                                t for t in team_check 
                                if t.lower() != team.get('team_name').lower()
                            ]
                csv_file.close()
                return {
                    "success": "File Uploaded and Teams Searched",
                    "status": status.HTTP_200_OK,
                    "missing_teams": team_check,
                    "files_uploaded": file_upload
                }
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error in team checking"
            )
    
        except Exception as exc:
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="An error has occurred"
            ) from exc

    async def add_teams_to_db(
        self,
        teams: List[items.NewTeam],
        number_of_runs: int
    ) -> Any:
        if teams:
            for team in teams:
                team_id = await self._generate_team_id()
                new_team_data = {
                    "team_id": team_id,
                    "team_name": team.team_name,
                    "city": "",
                    "division": team.division,
                    "conference": team.conference,
                    "division_rank": 0,
                    "overall_rank": 0,
                    "power_rankings": [team.power_ranking],
                    "win_ratio": 0.0,
                    "wins": 0,
                    "losses": 0,
                    "recent_opp": [0, 0, 0, 0, 0],
                    "season_opp": []
                }
                results = await self.sports_collection.update_one(
                    {self.level_constant.get('_id')},
                    {"teams": {"$push": new_team_data}},
                    upsert=True
                )
            return {
                "success": "Teams were added and algorithm was ran",
                "status": status.HTTP_200_OK,
                "number_of_files": results.modified_count
            }

    async def clear_season(self):
        query_base = {
            "_id": self.level_constant.get('_id')
        }
        await self.sports_collection.aggregate([
            {"$match": {**query_base}},
            {"$out": "previous_season"}
        ])
        update_params = {
            "$set": {
                "teams.$[].win_ratio": 0.0,
                "teams.$[].wins": 0,
                "teams.$[].losses": 0,
                "teams.$[].season_opp": []
            }
        }
        await self.sports_collection.update_one(query_base, update_params)

        last_pr = self.sports_collection.find_one(
            query_base,
            {"teams.power_ranking": {"$slice": -1}}
        )
        if last_pr and "teams" in last_pr:
            updates = []
            for team in last_pr["teams"]:
                if "power_ranking" in team and team["power_ranking"]:
                    last_rank = team["power_ranking"][-1]
                    updates.append(last_rank)
            cleared_seasons = await self.sports_collection.update_one(
                query_base,
                {"$set": {
                        f"teams.{i}.power_ranking": \
                            [updates[i]] for i, _ in enumerate(updates)
                    }
                }
            )

    async def _add_csv_file(
        self,
        query: dict,
        filename: str,
        csv_file: Any
    ) -> int:
        file_entry = {
            "filename": filename,
            "filedata": Binary(csv_file),
            "upload_date": str(datetime.datetime.today())
        }
        results = await self.csv_collection.update_one(
            query,
            {"$push": {"csv_files": file_entry}},
            upsert=True
        )
        return results.modified_count

    async def _find_teams(self, query: dict, teams_search: list) -> list:
        results = self.sports_collection.find(
            {**query, "teams": {"$nin": teams_search}},
            {"_id": 0}
        )
        return await results.to_list()

    async def _generate_team_id(self) -> int:
        teams = await self.sports_collection.find_one(
            {'_id': self.level_constant.get('_id')},
            sort=[("team_id", -1)],
            projection={"teams": 1, "_id": 0}
        )
        if teams:
            max_id = teams['team_id']
            new_team_id = max_id + 1
        else:
            new_team_id = 1
        return new_team_id

    async def retrieve_csv_file(self) -> Dict:
        csv_document = await self.csv_collection.find_one(
            {"_id": self.level_constant.get("_id")},
            {
                "csv_files": {"$slice": -1},
                "_id": 0
            }
        )
        return csv_document['csv_files'][0]
