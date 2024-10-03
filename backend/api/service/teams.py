#
# teams.py
#
# Location for database CRUD operations
# from JSON file.
#

# from bson.objectid import ObjectId
# from backend.api.utils.dependencies import get_database

from typing import Dict, List
import motor.motor_asyncio
from utils.json_helper import json_file_builder


MONGO_DETAILS = "mongodb://localhost:27017"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
database = client.sports_cluster
sports_collection = database.get_collection('sports_cluster')


async def add_sports_data(sport_doc: Dict):
    sport = await sports_collection.update_one(sport_doc, upsert=True)
    new_sport = await sports_collection.find_one({'_id': sport.updated_id})
    return json_file_builder(new_sport)


async def retrieve_sports(query: Dict):
    sports_teams: List = sports_collection.find(query)
    return sports_teams



# Function to retrieve sports data from MongoDB
async def retrieve_sports(query: Dict, id: int):
    # MongoDB lookup based on query
    sport = await sports_collection.find_one(query)
    if sport:
        return json_file_builder(sport)
    else:
        return None


async def update_sport():
    pass


async def delete_sport():
    pass
