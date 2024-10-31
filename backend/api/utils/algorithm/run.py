# Import the necessary functions from each module
from io import BytesIO
from typing import Tuple, List, Dict
from fastapi import HTTPException, status
from service.admin_teams import AdminTeamsService
from .upload import upload_csv
from .data_cleaning import clean_data
from .data_enrichment import enrich_data
from .main import run_calculations
# from .output import output_to_json
# from service.teams import retrieve_csv_file


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
        # self.output_to_db

    async def load_csv(self) -> None:
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
            {"teams": 1, "_id": 0}
        )
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No teams were found"
            )
        return document.get("teams")

    def data_cleaning(self) -> None:
        self.df = self.clean_data(self.df.copy(deep=True))

    async def data_enrichment(self) -> None:
        self.team_data = await self.retrieve_teams()
        self.df = self.enrich_data(
            self.df.copy(deep=True),
            self.team_services.level_constant.get("k_value"),
            self.team_services.level_constant.get("home_advantage"),
            self.team_services.level_constant.get("average_game_score"),
            self.team_data
        )

    def run_algorithm(self, itter: int) -> None:
        self.df = self.run_calculations(
            self.df.copy(deep=True),
            self.team_data,
            itter
        )

    async def execute(self, iterations: int):
        game_files = await self.load_csv()
        for game_file in game_files:
            csv_file = BytesIO(game_file["filedata"])
            self.df = upload_csv(csv_file)
            self.data_cleaning()
            await self.data_enrichment()
            await self.retrieve_teams()
            self.run_algorithm(iterations)


if __name__ == "__main__":
    # Example file paths for input and output
    input_csv_path = "CFootballEx.csv"
    output_json_path = "results.json"

    # Run the pipeline
    # main(input_csv_path, ('football', 'mens', 'college'))
