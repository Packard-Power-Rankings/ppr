#
# teams.py
#
# Location for database CRUD operations
# from JSON file.
#

# from bson.objectid import ObjectId
# from backend.api.utils.dependencies import get_database
import bson.binary
import datetime
from typing import Dict, List, Any
from fastapi import HTTPException
import motor.motor_asyncio
from utils.json_helper import json_file_builder
from fastapi import HTTPException

MONGO_DETAILS = \
    f"mongodb+srv://{os.getenv("MONGO_USER")}:{os.getenv("MONGO_PASS")}@" \
    "sports-cluster.mx1mo.mongodb.net/" \
    "?retryWrites=true&w=majority&appName=Sports-Cluster"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
database = client["sports_data"]
sports_collection = database.get_collection('teams_data')
csv_collection = database.get_collection('csv_files')


async def add_sports_data(query: Dict, team_data: Dict):
    """Adds Sports to Database

    Args:
        query (Dict): Query parameter for MongoDB
        team_data (Dict): Specific Team Data

    Returns:
        Integer: The number of Documents Entered
    """
    try:
        results = await sports_collection.update_one(
            query,
            {"$push": {"teams": team_data}},
            upsert=True
        )
        return results.modified_count
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=404, detail="Database error") from exc
    


# Adding CSV file storing into database
async def add_csv_file(query: Dict, csv_file: Any):
    """Adds CSV file into the database for faster algorithm
    calculations

    Args:
        query (Dict): Query for the Database
    """
    try:
        file_entry = {
            "file_name": csv_file.filename,
            "file_data": bson.binary.Binary(await csv_file.read()),
            "upload_date": str(datetime.datetime.today())
        }
        response = await csv_collection.update_one(
            query,
            {"$push": {"csv_files": file_entry}},
            upsert=True
        )
        return response.modified_count
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail="Database error"
        ) from exc


async def retrieve_csv_file(query: Dict):
    csv_document = await csv_collection.find_one(
        query,
        {
            "csv_files": {"$slice": -1},
            "_id": 0
        }
    )
    return csv_document['csv_files'][0]


# Function to retrieve sports data from MongoDB
# Changed id to mongo_id because it is overriding a builtin function
async def retrieve_sports(query: Dict, projection: Dict | None):
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
    return result.modified_count


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
