# from io import BytesIO
# from run import MainAlgorithm
# import pytest
# import sys
# from unittest.mock import AsyncMock, MagicMock, patch

# # Mock the `service` module
# sys.modules['service'] = MagicMock()
# sys.modules['service.admin_teams'] = MagicMock()


# @pytest.fixture
# def mock_team_services():
#     team_services = MagicMock()
#     team_services.level_constant = {
#         "k_value": 30,
#         "home_advantage": 50,
#         "average_game_score": 200,
#         "_id": "some_id"
#     }
#     team_services.retrieve_csv_file = AsyncMock(return_value=[
#         {"filedata": b"2023-11-19,Team A,Team B,100,90,0\n2023-11-20,Team C,Team D,95,85,999"}
#     ])
#     team_services.sports_collection.find_one = AsyncMock(return_value={
#         "teams": [
#             {"team_name": "Team A", "power_ranking": [1500]},
#             {"team_name": "Team B", "power_ranking": [1400]},
#             {"team_name": "Team C", "power_ranking": [1300]},
#             {"team_name": "Team D", "power_ranking": [1200]},
#         ]
#     })
#     return team_services


# @pytest.fixture
# def main_algorithm(mock_team_services):
#     return MainAlgorithm(team_services=mock_team_services, level_key=('football', 'mens', 'college'))


# @patch("run.upload_csv", return_value=None)
# @patch("run.clean_data", return_value=None)
# @patch("run.enrich_data", return_value=None)
# @patch("run.run_calculations", return_value=(None, None))
# @patch("run.update_teams", new_callable=AsyncMock)
# async def test_execute_pipeline(mock_update_teams, mock_run_calculations, mock_enrich_data, mock_clean_data, mock_upload_csv, main_algorithm):
#     await main_algorithm.execute(1)

#     # Ensure the full pipeline was executed
#     mock_upload_csv.assert_called_once()
#     mock_clean_data.assert_called_once()
#     mock_enrich_data.assert_called_once()
#     mock_run_calculations.assert_called_once()
#     mock_update_teams.assert_called_once()


# @pytest.mark.asyncio
# async def test_load_csv(main_algorithm):
#     csv_content = await main_algorithm.load_csv()
#     assert len(csv_content) == 1
#     assert "filedata" in csv_content[0]


# @pytest.mark.asyncio
# async def test_retrieve_teams(main_algorithm):
#     teams = await main_algorithm.retrieve_teams()
#     assert len(teams) == 4
#     assert teams[0]["team_name"] == "Team A"


# # def test_data_cleaning(main_algorithm):
# #     with patch("run.clean_data", return_value="cleaned_df") as mock_clean_data:
# #         main_algorithm.df = "raw_df"
# #         main_algorithm.data_cleaning()
# #         mock_clean_data.assert_called_once_with("raw_df")
# #         assert main_algorithm.df == "cleaned_df"


# @pytest.mark.asyncio
# async def test_data_enrichment(main_algorithm):
#     with patch("run.enrich_data", return_value="enriched_df") as mock_enrich_data:
#         await main_algorithm.data_enrichment()
#         mock_enrich_data.assert_called_once_with(
#             main_algorithm.df,
#             30,  # k_value
#             50,  # home_advantage
#             200,  # average_game_score
#             main_algorithm.team_data
#         )
#         assert main_algorithm.df == "enriched_df"


# @pytest.mark.asyncio
# async def test_update_db(main_algorithm):
#     with patch("run.update_teams", new_callable=AsyncMock) as mock_update_teams:
#         await main_algorithm.update_db()
#         mock_update_teams.assert_called_once_with(
#             main_algorithm.df,
#             main_algorithm.team_data,
#             main_algorithm.team_services.sports_collection,
#             main_algorithm.team_services.level_constant
#         )


# # def test_run_algorithm(main_algorithm):
# #     with patch("run.run_calculations", return_value=("calculated_df", "calculated_teams")) as mock_run_calculations:
# #         main_algorithm.df = "raw_df"
# #         main_algorithm.team_data = "raw_team_data"
# #         main_algorithm.run_algorithm()
# #         mock_run_calculations.assert_called_once_with(
# #             "raw_df", "raw_team_data")
# #         assert main_algorithm.df == "calculated_df"
# #         assert main_algorithm.team_data == "calculated_teams"
