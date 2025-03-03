# Import the necessary functions from each module
from io import BytesIO
from typing import Tuple, List
import asyncio
from fastapi import HTTPException, status
from api.service.admin_teams import AdminTeamsService
from .upload import upload_csv
from .data_cleaning import clean_data
from .data_enrichment import enrich_data
from .main import run_calculations, calculate_z_scores
from .output import update_teams, set_z_scores


class MainAlgorithm():
    def __init__(
        self,
        team_services: AdminTeamsService,
        level_key: Tuple
    ) -> None:
        self.team_services = team_services
        self.level_key = level_key
        self.df = None
        self.team_data = []
        self.upload_csv = upload_csv
        self.clean_data = clean_data
        self.enrich_data = enrich_data
        self.run_calculations = run_calculations
        self.output_to_db = update_teams
        self.set_z_scores = set_z_scores
        self.calculate_z_scores = calculate_z_scores

    async def load_csv(self):
        csv_content = await self.team_services.retrieve_csv_file()
        if not csv_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CSV file was not found"
            )
        return csv_content

    @property
    def team_collection(self) -> List:
        return self.team_data

    @team_collection.setter
    def team_collection(self, teams_list) -> None:
        self.team_data = teams_list

    async def retrieve_teams(self) -> List:
        document: dict = await self.team_services.sports_collection.find_one(
            {"_id": self.team_services.level_constant.get("_id")},
            {
                "teams.team_id": 1,
                "teams.team_name": 1,
                "teams.power_ranking": {"$slice": -1},  # Get only the last power_ranking element
                "teams.recent_opp": 1,
                "_id": 0
            }
        )
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No teams were found"
            )
        teams = document.get("teams", [])

        for team in teams:
            if "power_ranking" in team and team["power_ranking"]:
                last_ranking = team["power_ranking"][0]  # Get the first (and only) item
                # Extract the first value regardless of key name
                if last_ranking:
                    team["power_ranking"] = [next(iter(last_ranking.values()))]

        return teams

    def data_cleaning(self) -> None:
        self.df = self.clean_data(self.df)

    async def data_enrichment(self) -> None:
        self.team_data = await self.retrieve_teams()
        self.df = self.enrich_data(
            self.df,
            self.team_services.level_constant.get("k_value"),
            self.team_services.level_constant.get("home_advantage"),
            self.team_services.level_constant.get("average_game_score"),
            self.team_data
        )

    async def update_db(self, date: str):
        await self.output_to_db(
            self.df,
            self.team_data,
            self.team_services.sports_collection,
            self.team_services.level_constant,
            date
        )

    def run_algorithm(self):
        self.df, self.team_data = self.run_calculations(
            self.df,
            self.team_data
        )

    async def execute_z_score_calc(self):
        await self.retrieve_teams()
        game_files = await self.load_csv()
        for game_file in game_files:
            csv_file = BytesIO(game_file["filedata"])
            self.df = upload_csv(csv_file)
            self.data_cleaning()
            await self.data_enrichment()
        n = 2 * len(self.df.index)
        self.df = self.calculate_z_scores(self.df, n)
        await self.set_z_scores(
            self.df,
            self.team_data,
            self.team_services.sports_collection,
            self.team_services.level_constant
        )
        self.df = self.df.iloc[0:0]

    async def execute_algo(self, iterations: int):
        await self.retrieve_teams()
        game_files = await self.load_csv()
        date = game_files[-1]['sports_week']
        for _ in range(iterations):
            # await self.update_db(date)
            for game_file in game_files:
                csv_file = BytesIO(game_file["filedata"])
                self.df = upload_csv(csv_file)
                self.data_cleaning()
                await self.data_enrichment()
                self.run_algorithm()
                await self.update_db(date)
                self.df = self.df.iloc[0:0]
            await asyncio.sleep(0.5)


if __name__ == "__main__":
    # Example file paths for input and output
    input_csv_path = "CFootballEx.csv"
    output_json_path = "results.json"

    # Run the pipeline
    # main(input_csv_path, ('football', 'mens', 'college'))
