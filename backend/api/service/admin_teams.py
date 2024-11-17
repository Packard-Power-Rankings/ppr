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

MONGO_DETAILS = \
    f"mongodb+srv://{os.getenv("MONGO_USER")}:{os.getenv("MONGO_PASS")}@" \
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
        self.sports_collection = database.get_collection('temp')
        self.csv_collection = database.get_collection('csv_files_temp')
        self.previous_season = database.get_collection('previous_season')
        self.level_key = level_key
        self.level_constant = LEVEL_CONSTANTS[level_key]
        # self.teams_check: List[Dict[str, str]] = []
        # self.main_algorithm = MainAlgorithm(self, level_key)

    async def store_csv_check_teams(
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

            # Creates a list for teams to check in db
            team_check: List[str] = []
            for team in csv_reader:
                team_check.append(team[1].lower())
                team_check.append(team[2].lower())

            query_teams = {
                "_id": self.level_constant.get('_id')
            }
            results = await self._find_teams(query_teams, team_check)
            # If the results are not empty loop through and see
            # which teams are not in the database and return the
            # list of the teams that need to be added
            if results:
                teams: List[Dict[str, str]] = results[0].get('teams')
                for team in teams:
                    if team.get('team_name').lower() in [t.lower() for t in team_check]:
                        team_check = [
                            t for t in team_check 
                            if t.lower() != team.get('team_name').lower()
                        ]

            # Close the CSV file after processing
            await csv_file.close()

            return {
                "success": "File Uploaded and Teams Searched",
                "status": status.HTTP_200_OK,
                "missing_teams": team_check,
                "files_uploaded": file_upload
            }
        
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
        message = {}
        team_id = await self._generate_team_id()
        for team in teams:
            team_id = team_id + 1
            new_team_data = {
                "team_id": team_id,
                "team_name": team.get("team_name"),
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
            results = await self.sports_collection.update_one(
                {
                    "_id": self.level_constant.get('_id'),
                    "teams.team_name": {"$ne": team.get("team_name")}
                },
                {"$addToSet": {"teams": new_team_data}}
            )
        if results.modified_count > 0:
            message.update(
                message="Teams were added",
                status=status.HTTP_200_OK,
                number_of_files=results.modified_count
            )
        else:
            message.update(
                message="Team already exists",
                status=status.HTTP_200_OK,
                number_of_files=results.modified_count
            )
        return message

    async def run_main_algorithm(self, iterations: int):
        """Runs the main algorithm

        Args:
            iterations (int): Number of times to run
            the algorithm
        """
        from utils.algorithm.run import MainAlgorithm
        algorithm = MainAlgorithm(self, self.level_key)
        await algorithm.execute(iterations)

    async def calculate_z_scores(self):
        from utils.algorithm.run import MainAlgorithm
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
        date: str
    ):
        query = {
            "sport_type": self.level_key[0],
            "gender": self.level_key[1],
            "level": self.level_key[2]
        }
        csv_content = await self.csv_collection.find_one(
            query,
            {"csv_files": {"$elemMatch": {"sports_week": date}}}
        )
        print(csv_content)
        csv_data = csv_content['csv_files'][0]
        csv_file_data = csv_data['filedata']
        csv_stream = StringIO(csv_file_data.decode('utf-8'))

        csv_reader = csv.reader(csv_stream)
        rows = list(csv_reader)

        for row in rows:
            if row[1] == home_team and row[2] == away_team:
                row[3] = home_score
                row[4] = away_score
                break

        output_stream = StringIO()
        csv_writer = csv.writer(output_stream)
        csv_writer.writerows(rows)

        updated_csv_file = output_stream.getvalue().encode('utf-8')
        updated_results = await self.csv_collection.update_one(
            query,
            {"$set": {"csv_files.$[elem].filedata": updated_csv_file}},
            array_filters=[{"elem.sports_week": date}]
        )
        # print(updated_results.modified_count)
        await self.update_db_data(
            home_team,
            home_score,
            away_team,
            away_score,
            f"{home_team}_{away_team}_{date}"
        )

    async def clear_season(self):
        """Clears the season at the end of a season
        and stores the previous season in a separate
        database
        """
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
        if teams:
            max_id = \
                max(team['team_id'] \
                    for team in teams["teams"] if 'team_id' in team)
            new_team_id = max_id
        else:
            new_team_id = 1
        return new_team_id

    async def retrieve_csv_file(self) -> Dict:
        """Retrieves the CSV file from the database

        Returns:
            Dict: Returns the contents recieved from
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
