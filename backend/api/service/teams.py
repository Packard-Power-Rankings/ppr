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


async def add_sports_data(query: Dict, team_data: Dict):
    """Adds Sports to Database

    Args:
        query (Dict): Query parameter for MongoDB
        team_data (Dict): Specific Team Data

    Returns:
        Integer: The number of Documents Entered
    """
    results = await sports_collection.update_one(
        query,
        {"$push": {"teams": team_data}}
    )
    return results.modified_count()


# Adding CSV file storing into database
async def add_csv_file(query: Dict):
    """Adds CSV file into the database for faster algorithm
    calculations

    Args:
        query (Dict): Query for the Database
    """
    pass


# Function to retrieve sports data from MongoDB
# Changed id to mongo_id because it is overriding a builtin function
async def retrieve_sports(query: Dict, projection: Dict | None = None):
    """
    Retrieves sports or teams data from the MongoDB collection.

    Args:
        query (Dict): The query filter for MongoDB.
        projection (Dict | None): Fields to include or exclude (optional).

    Returns:
        Dict | None: Returns the document or None if no match is found.
    """
    try:
        if projection:
            sport_data = await sports_collection.find_one(query, projection)
        else:
            sport_data = await sports_collection.find_one(query)

        if sport_data:
            return sport_data
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database error") from e


async def update_sport(query: Dict, update_data: Dict):
    """Updates information based off the specific query
    in the database

    Args:
        query (Dict): Search Parameters for Database
        update_data (Dict): What is Being Updated

    Returns:
        Integer: Returns the count of documents updated
    """
    result = await sports_collection.update_one(query, update_data)
    return result.modified_count()


async def delete_sport(query: Dict):
    result = await sports_collection.update_one(
        query,
        {"$unset": {"teams": ""}}
    )
    if result.modified_count() > 0:
        return "Removed Teams From Database"
    return "No Teams Were Found"


async def clear_season(
    query: Dict,
    update_params: Dict,
    array_filters: List[Dict]
):
    result = await sports_collection.update_one(
        query,
        update_params,
        array_filters
    )
    return result
