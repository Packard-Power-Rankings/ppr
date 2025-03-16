"""Logical operations for Admin
"""


import os
import io
import asyncio
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
            found_team_names = {team["team_name"] for doc in documents for team in doc["teams"] if "team_name" in team}

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
                message="Teams were added successfully",
                status=status.HTTP_200_OK,
                number_of_files=results.modified_count
            )
        else:
            message.update(
                message="Team already exists in the database",
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
        date: str
    ):
        """Updates the CSV file and database based
        on the new data that has been passed in.
        Does not run algorithm.

        Args:
            home_team (str): Home Team Name
            home_score (int): Updated Home Score
            away_team (str): Away Team Name
            away_score (int): Updated Away Score
            date (str): Game Date The Two Teams played
        """
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

    async def update_team_name(
        self,
        team_id: int,
        new_team_name: str
    ):
        """
        Updates a teams name in both the database and csv files
        """

        query_base = {
            "_id": self.level_constant.get('_id'),
            "sport_type": self.level_key[0],
            "gender": self.level_key[1],
            "level": self.level_key[2]
        }

        await self.sports_collection.update_one(
            {**query_base, "teams.team_id": team_id},
            {
                "$set": {"teams.$.team_name": new_team_name}
            }
        )

        await self.sports_collection.update_many(
            {**query_base, "teams.season_opp.opponent_id": team_id},
            {"$set": {"teams.$[].season_opp.$[elem].opponent_name": new_team_name}},
            array_filters=[{"elem.opponent_id": team_id}]
        )

        query_base2 = {
            "sport_type": self.level_key[0],
            "gender": self.level_key[1],
            "level": self.level_key[2]
        }
        team_doc = await self.csv_collection.find_one(query_base2)
        if not team_doc or "csv_files" not in team_doc:
            print("No CSV files found for this query.")
            return

        updated_csv_files = []

        for csv_file in team_doc["csv_files"]:
            filename = csv_file["filename"]
            filedata = base64.b64decode(csv_file["filedata"])

            decoded_filedata = filedata.decode("utf-8", errors="replace")
            df = pd.read_csv(io.StringIO(decoded_filedata))

            # Replace old team name with new team name in all occurrences
            df.replace(to_replace={"team_name": {team_id: new_team_name},
                                "opponent_name": {team_id: new_team_name}},
                    inplace=True)

            output = io.BytesIO()
            df.to_csv(output, index=False)
            new_filedata = base64.b64encode(output.getvalue()).decode('utf-8')

            updated_csv_files.append({
                "filename": filename,
                "filedata": new_filedata,
                "upload_date": csv_file.get("upload_date"),  # Preserve original upload_date
                "sports_week": csv_file.get("sports_week", "")
            })

        self.csv_collection.update_one(
            query_base,
            {"$set": {"csv_files": updated_csv_files}}
        )


        return {
            "results": f"Team {new_team_name} has been updated"
        }

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
                                                {"$gt": [{"$size": "$$team.power_ranking"}, 0]},
                                                [{"$arrayElemAt": ["$$team.power_ranking", -1]}],
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
                        'game_id': game.get('game_id')
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
                new_filedata_binary = bson.Binary(new_csv_string.encode("utf-8"))

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

    async def delete_team(
        self,
        team_name: str,
        team_id: int
    ):
        # Needs to delete the team from the sports data collection
        # Before the removal, need to get the array of opp ids and
        # game dates. Makes removal faster for season_opp array and
        # csv file deletions. Also, need to increment/decrement wins/losses

        pipeline = [
            {"$match": {  # Find the correct document
                "_id": self.level_constant.get('_id'),
                "sport_type": self.level_key[0],
                "gender": self.level_key[1],
                "level": self.level_key[2],
                "teams.team_id": team_id,
                "teams.team_name": team_name
            }},
            {"$unwind": "$teams"},
            {"$match": {"teams.team_id": team_id}},
            {"$unwind": "$teams.season_opp"},
            {"$project": {
                "_id": 0,
                "opponent_id": "$teams.season_opp.opponent_id",
                "game_date": "$teams.season_opp.game_date"
            }}
        ]

        try:
            team_data = await self.sports_collection.aggregate(pipeline).to_list(None)
            if not team_data:
                return {"message": "Team not found", "status": status.HTTP_404_NOT_FOUND}

            opponent_ids = [item["opponent_id"] for item in team_data]
            game_dates = [item["game_date"] for item in team_data]

            for opponent_id in opponent_ids:
                # Find the opponent team's document
                query = {
                    "_id": self.level_constant.get('_id'),
                    "sport_type": self.level_key[0],
                    "gender": self.level_key[1],
                    "level": self.level_key[2],
                    "teams.team_id": opponent_id
                }

                opponent_team = await self.sports_collection.find_one(query)

                if opponent_team:
                    for team in opponent_team["teams"]:
                        if team["team_id"] == opponent_id:
                            for game in team.get("season_opp", []):
                                if game["opponent_id"] == team_id:
                                    # Step 2a: Decrement wins/losses
                                    if game["home_team"] == 1:  # Check if deleted team was home
                                        winner = team_id if game["home_score"] > game["away_score"] else game["opponent_id"]
                                    else:
                                        winner = team_id if game["away_score"] > game["home_score"] else game["opponent_id"]

                                    if winner == team_id:
                                        update = {"$inc": {"teams.$.losses": -1}}  # Deleted team won, opponent lost
                                    else:
                                        update = {"$inc": {"teams.$.wins": -1}}  # Deleted team lost, opponent won

                                    await self.sports_collection.update_one(query, update)

                                    # Step 2b: Remove the game from `season_opp`
                                    update_remove_game = {
                                        "$pull": {"teams.$.season_opp": {"opponent_id": team_id}}
                                    }
                                    await self.sports_collection.update_one(query, update_remove_game)

            for game_date in set(game_dates):
                query_csv = {
                    "_id": self.level_constant.get('_id'),
                    "sport_type": self.level_key[0],
                    "gender": self.level_key[1],
                    "level": self.level_key[2],
                    "csv_files.sports_week": game_date
                }

                csv_document = await self.sports_collection.find_one(query_csv, {"csv_files.$": 1})

                if csv_document and "csv_files" in csv_document:
                    csv_file = csv_document["csv_files"][0]  # Only one file matches

                    # Decode the CSV and remove rows containing `team_name`
                    csv_string = csv_file["filedata"].decode("utf-8")
                    df = pd.read_csv(io.StringIO(csv_string), header=None)
                    df_filtered = df[~df.iloc[:, 1].isin([team_name])]

                    # Convert back to CSV and update MongoDB
                    new_csv_string = df_filtered.to_csv(index=False, header=False)
                    new_filedata_binary = bson.Binary(new_csv_string.encode("utf-8"))

                    await self.sports_collection.update_one(
                        query_csv,
                        {"$set": {"csv_files.$.filedata": new_filedata_binary}}
                    )

            # Step 4: Delete the team itself from the teams array
            query_delete_team = {
                "_id": self.level_constant.get('_id'),
                "sport_type": self.level_key[0],
                "gender": self.level_key[1],
                "level": self.level_key[2]
            }
            update_delete_team = {"$pull": {"teams": {"team_id": team_id}}}

            await self.sports_collection.update_one(query_delete_team, update_delete_team)

            return {"message": "Team successfully deleted", "status": status.HTTP_200_OK}
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
            {"$push": { "flagged_games": {
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
