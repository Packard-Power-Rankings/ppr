"""Mongo-backed ranking and z-score orchestration."""

from typing import List, Tuple

import pandas as pd
from fastapi import HTTPException, status

from api.service.admin_teams import AdminTeamsService
from api.service.game_ingestion import GAME_COLUMNS
from .data_cleaning import clean_data
from .data_enrichment import enrich_data
from .main import calculate_z_scores, run_calculations
from .output import set_z_scores, update_teams


class MainAlgorithm:
    def __init__(
        self,
        team_services: AdminTeamsService,
        level_key: Tuple,
    ) -> None:
        self.team_services = team_services
        self.level_key = level_key
        self.df = None
        self.team_data = []
        self.clean_data = clean_data
        self.enrich_data = enrich_data
        self.run_calculations = run_calculations
        self.output_to_db = update_teams
        self.set_z_scores = set_z_scores
        self.calculate_z_scores = calculate_z_scores

    async def load_games(self) -> List[dict]:
        games = await self.team_services.retrieve_games()
        if not games:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No games were found for the selected dataset",
            )
        return games

    @staticmethod
    def games_dataframe(games: List[dict]) -> pd.DataFrame:
        """Adapt canonical Mongo records to the algorithm's tabular contract."""
        return pd.DataFrame(
            [
                {
                    "date": game["game_date"],
                    "home_team": game["home_team"],
                    "away_team": game["away_team"],
                    "home_score": game["home_score"],
                    "away_score": game["away_score"],
                    "neutral_site": game["neutral_site"],
                }
                for game in games
            ],
            columns=GAME_COLUMNS,
        )

    @property
    def team_collection(self) -> List:
        return self.team_data

    @team_collection.setter
    def team_collection(self, teams_list) -> None:
        self.team_data = teams_list

    @staticmethod
    def _ranking_value(team: dict, use_initial: bool) -> float:
        rankings = team.get("power_ranking") or []
        if not rankings:
            return 0.0
        entry = rankings[0] if use_initial else rankings[-1]
        if not entry:
            return 0.0
        return float(next(iter(entry.values())))

    async def retrieve_teams(self, use_initial: bool = False) -> List[dict]:
        document: dict = await self.team_services.sports_collection.find_one(
            {"_id": self.team_services.level_constant.get("_id")},
            {
                "teams.team_id": 1,
                "teams.team_name": 1,
                "teams.division": 1,
                "teams.conference": 1,
                "teams.overall_rank": 1,
                "teams.power_ranking": 1,
                "teams.season_initial_power": 1,
                "teams.recent_opp": 1,
                "_id": 0,
            },
        )
        if not document or not document.get("teams"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No teams were found",
            )

        teams = document["teams"]
        for team in teams:
            initial_ranking = self._ranking_value(team, True)
            season_initial_power = team.get("season_initial_power")
            if use_initial and isinstance(season_initial_power, dict) \
                    and season_initial_power:
                initial_ranking = float(next(iter(
                    season_initial_power.values()
                )))
            selected_ranking = (
                initial_ranking
                if use_initial
                else self._ranking_value(team, False)
            )
            team["initial_power_ranking"] = initial_ranking
            team["power_ranking"] = [selected_ranking]
            if use_initial:
                team["recent_opp"] = [0, 0, 0, 0, 0]
            else:
                recent = list(team.get("recent_opp") or [])[:5]
                team["recent_opp"] = recent + [0] * (5 - len(recent))
        return teams

    def data_cleaning(self) -> None:
        self.df = self.clean_data(self.df)

    def data_enrichment(self) -> None:
        self.df = self.enrich_data(
            self.df,
            self.team_services.level_constant.get("k_value"),
            self.team_services.level_constant.get("home_advantage"),
            self.team_services.level_constant.get("average_game_score"),
            self.team_data,
        )

    def run_algorithm(self) -> None:
        self.df, self.team_data = self.run_calculations(
            self.df,
            self.team_data,
        )

    async def execute_z_score_calc(
        self,
        games: List[dict] | None = None,
        teams: List[dict] | None = None,
    ) -> None:
        games = games or await self.load_games()
        self.team_data = teams or await self.retrieve_teams()
        self.df = self.games_dataframe(games)
        self.data_cleaning()
        self.data_enrichment()
        self.df = self.calculate_z_scores(self.df, 2 * len(self.df.index))
        await self.set_z_scores(
            self.df,
            self.team_data,
            self.team_services.sports_collection,
            self.team_services.games_collection,
            self.team_services.level_constant,
            self.team_services.level_key,
        )

    async def execute_algo(self, iterations: int) -> None:
        if iterations < 1 or iterations > 100:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Iterations must be between 1 and 100",
            )

        games = await self.load_games()
        self.team_data = await self.retrieve_teams(use_initial=True)
        for _ in range(iterations):
            self.df = self.games_dataframe(games)
            self.data_cleaning()
            self.data_enrichment()
            self.run_algorithm()

        ranking_date = max(game["game_date"] for game in games)
        await self.output_to_db(
            self.df,
            self.team_data,
            self.team_services.sports_collection,
            self.team_services.level_constant,
            ranking_date,
        )

        # A ranking run is a complete pipeline. The standalone z-score action
        # remains available when an admin only needs to refresh z-scores.
        await self.execute_z_score_calc(games=games, teams=self.team_data)
