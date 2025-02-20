import os
from typing import Tuple, Dict, List
from math import e
import motor.motor_asyncio
from fastapi import status, HTTPException
from api.config.constants import LEVEL_CONSTANTS
from api.utils.json_helper import query_params_builder


MONGO_DETAILS = \
    f"mongodb+srv://{os.getenv("MONGO_USER")}:{os.getenv("MONGO_PASS")}@" \
    "sports-cluster.mx1mo.mongodb.net/" \
    "?retryWrites=true&w=majority&appName=Sports-Cluster"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
database = client["sports_data"]


class UsersServices():
    def __init__(self, level_key: Tuple):
        self.user_collection = database.get_collection('temp')
        self.level_constants = LEVEL_CONSTANTS[level_key]
        self.level_key = level_key
        self.sports_data = []
        
    async def retrieve_sports_info(self):
        query: Dict = query_params_builder()
        query.update(
            _id=self.level_constants.get('_id'),
            sport_type=self.level_key[0],
            gender=self.level_key[1],
            level=self.level_key[2]
        )
        projection = {
            "teams": 1,
            "_id": 0
        }
        pipeline = [
            {"$match": query},
            {"$unwind": "$teams"},
            {"$project": {
                "_id": 0,
                "team": {
                    "overall_rank": "$teams.overall_rank",
                    "team_name": "$teams.team_name",
                    "power_ranking": {"$slice": ["$teams.power_ranking", -1]},
                    "division_rank": "$teams.division_rank",
                    "division": "$teams.division",
                    "wins": "$teams.wins",
                    "losses": "$teams.losses"
                }
            }},
            {"$group": {
                "_id": None,
                "teams": {"$push": "$team"}
            }},
            {"$project": {
                "_id": 0,
                "teams": 1
            }}
        ]

        return await self._sports_retrieval(pipeline)

    async def retrieve_team_info(self, team_name):
        query: Dict = query_params_builder()
        query.update(
            _id=self.level_constants.get('_id'),
            sport_type=self.level_key[0],
            gender=self.level_key[1],
            level=self.level_key[2],
            teams={
                "$elemMatch": {
                    "team_name": {"$regex": f"^{team_name}$", "$options": "i"}
                }
            }
        )

        projection = {
            "teams.$": 1,
            "_id": 0
        }
        return await self._sports_retrieval(query, projection)

    @staticmethod
    def sigmond_curve(vabs) -> float:
        return 1.0 / (1.0 + 40.0 * e ** (-1.0 * ((vabs / 6.0) + 2.0)))

    @staticmethod
    def find_matching_games(season_opp: List, team_name: str) -> bool:
        return any(
            team_name.lower() == game['opponent_name'].lower()
            for game in season_opp
        )

    async def score_predictions(
        self,
        home_team: str,
        away_team: str,
        home_field_adv: bool
    ) -> Dict[str, float]:
        team_name_list = [home_team, away_team]
        home_team_data, away_team_data = \
            await self._retrieve_team_info(team_name_list)

        vabs = 0
        if home_field_adv:
            vabs += abs(
                (next(iter(home_team_data['power_ranking'][-1].values())) + \
                self.level_constants.get('home_advantage')) - \
                    next(iter(away_team_data['power_ranking'][-1].values()))
            )
        else:
            vabs += abs(
                next(iter(home_team_data['power_ranking'][-1].values())) - \
                    next(iter(away_team_data['power_ranking'][-1].values()))
            )
        vbev = ((((vabs + 2) ** 0.45) - 1.0) ** (20.0/9.0)) - 2
        new_vbev = max(vbev, 0)
        p_value = self.sigmond_curve(vabs)

        mov1 = p_value * new_vbev + (1 - p_value) * new_vbev
        win1 = self.level_constants.get('average_game_score') / 2 + \
            0.5 * mov1
        los1 = self.level_constants.get('average_game_score') - win1

        ave = 0
        if not self.find_matching_games(home_team_data['season_opp'], away_team):
            ave += self.level_constants.get('average_game_score')
        else:
            home_season_list = home_team_data['season_opp']
            away_season_list = away_team_data['season_opp']

            home_game_totals = 0
            for home_game in home_season_list:
                if home_game['home_team']:
                    home_game_totals += home_game['home_score']
                else:
                    home_game_totals += home_game['away_score']

            away_game_totals = 0
            for away_game in away_season_list:
                if away_game['home_team']:
                    away_game_totals += away_game['home_score']
                else:
                    away_game_totals += away_game['away_score']

            home_games_played = len(home_team_data['season_opp'])
            away_games_played = len(away_team_data['season_opp'])

            ave += \
                (home_game_totals + away_game_totals) / \
                    (home_games_played + away_games_played)

        win2 = (10 * ave + 9 * win1 - 10 * los1) / 19
        los2 = ave - win2
        mov2 = win2 - los2

        mov3 = (ave / self.level_constants.get("average_game_score")) * mov1
        mov3 = max(mov2, mov3)

        if self.level_constants.get("average_game_score") < ave:
            mov3 = mov2

        win3 = (ave + mov3) / 2
        los3 = ave - win3

        if los3 < 0:
            win3 += abs(los3)
            los3 += abs(los3)

        home_pr = next(iter(home_team_data['power_ranking'][-1].values()))
        away_pr = next(iter(away_team_data['power_ranking'][-1].values()))

        if home_field_adv:
            if home_pr + self.level_constants.get('home_advantage') < away_pr:
                return {f"{home_team}": los3, f"{away_team}": win3}
        else:
            if home_pr < away_pr:
                return {f"{home_team}": los3, f"{away_team}": win3}
        return {f"{home_team}": win3, f"{away_team}": los3}

    @property
    def sports_teams(self) -> List:
        return self.sports_data

    @sports_teams.setter
    def sports_teams(self, sports_data: List) -> None:
        self.sports_data = sports_data

    async def _retrieve_team_info(self, team_name_list: List):
        team_names_lower = [names.lower() for names in team_name_list]
        results = await self.user_collection.find_one(
            {"_id": self.level_constants.get("_id")},
            {
                "_id": 0,
                "teams": {
                    "$filter": {
                        "input": "$teams",
                        "as": "team",
                        "cond": {
                            "$in": [
                                {
                                    "$toLower": "$$team.team_name"
                                },team_names_lower
                            ]
                        }
                    }
                }
            }
        )
        team_list = results['teams']
        team_one, team_two = team_list
        if team_names_lower[0] == team_one['team_name'].lower():
            return team_one, team_two
        return team_two, team_one
        
    async def _sports_retrieval(self, pipeline: list):
        try:
            cursor = self.user_collection.aggregate(pipeline)
            result = await cursor.to_list(length=None)
            if result and len(result) > 0:
                return {
                    "message": "Successfully Found Teams",
                    "status": status.HTTP_200_OK,
                    "data": result[0]  # First document contains our grouped results
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
