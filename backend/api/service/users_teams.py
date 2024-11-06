import os
from typing import Tuple, Dict, List
import motor.motor_asyncio
from fastapi import status, HTTPException
from config.config import LEVEL_CONSTANTS
from utils.json_helper import query_params_builder


MONGO_DETAILS = \
    f"mongodb+srv://{os.getenv("MONGO_USER")}:{os.getenv("MONGO_PASS")}@" \
    "sports-cluster.mx1mo.mongodb.net/" \
    "?retryWrites=true&w=majority&appName=Sports-Cluster"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
database = client["sports_data"]


class UsersServices():
    def __init__(self, level_key: Tuple):
        self.user_collection = database.get_collection('temp1')
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
        projection = {"teams": 1, "_id": 0}
        return await self._sports_retrieval(query, projection)

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

    @property
    def sports_teams(self) -> List:
        return self.sports_data

    @sports_teams.setter
    def sports_teams(self, sports_data: List) -> None:
        self.sports_data = sports_data
        
    async def _sports_retrieval(self, query: Dict, projection: Dict):
        try:
            self.sports_data = await self.user_collection.find_one(
                query,
                projection
            )
            if self.sports_data:
                return {
                    "message": "Succesfully Found Teams",
                    "status": status.HTTP_200_OK,
                    "data": self.sports_data
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
