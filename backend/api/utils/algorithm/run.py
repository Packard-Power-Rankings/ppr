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


# async def main(level_key: Tuple):
#     """
#     Main orchestration function to run the entire pipeline.
#     :param file_path: Path to the input CSV file.
#     :param output_file: Path to the output JSON file.
#     """
    
#     # Step 1: Upload and validate CSV
#     query = {
#         "sport_type": level_key[0],
#         "gender": level_key[1],
#         "level": level_key[2]
#     }
#     csv_file = await retrieve_csv_file(query)
#     if not csv_file:
#         raise HTTPException(status_code=404, detail="No CSV file found")

#     csv_content = BytesIO(csv_file['file_data'])
#     df = upload_csv(csv_content)
#     if df is None:
#         raise HTTPException(status_code=400, detail='No CSV file found')

#     # Step 2: Clean the data
#     df = clean_data(df)

#     # Step 3: Enrich the data with dummy values
#     df = enrich_data(df, level_key)

#     # Step 4: Run the core calculations (power difference, Z-scores, etc.)
#     df = run_calculations(df, level_key)

#     # Step 5: Output the final results to JSON
#     await output_to_json(df, level_key)


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
        csv_file = BytesIO(csv_content['filedata'])
        self.df = self.upload_csv(csv_file)
        # print("After loading CSV:", self.df['neutral_site'].to_string())

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
        # print("After data cleaning:", self.df['neutral_site'].to_string())

    async def data_enrichment(self) -> None:
        self.team_data = await self.retrieve_teams()
        self.df = self.enrich_data(
            self.df.copy(deep=True),
            self.team_services.level_constant.get("k_value"),
            self.team_services.level_constant.get("home_advantage"),
            self.team_services.level_constant.get("average_game_score"),
            self.team_data
        )
        # print("After data enrichment:", self.df['neutral_site'].to_string())

    def run_algorithm(self, itter: int) -> None:
        self.df = self.run_calculations(
            self.df.copy(deep=True),
            self.team_data,
            itter
        )

    async def execute(self, itter: int):
        await self.load_csv()
        self.data_cleaning()
        await self.data_enrichment()
        await self.retrieve_teams()
        self.run_algorithm(itter)


if __name__ == "__main__":
    # Example file paths for input and output
    input_csv_path = "CFootballEx.csv"
    output_json_path = "results.json"

    # Run the pipeline
    # main(input_csv_path, ('football', 'mens', 'college'))
