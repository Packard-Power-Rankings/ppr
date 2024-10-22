#
# teams.py
#
# Location for database CRUD operations
# from JSON file.
#

# from bson.objectid import ObjectId
# from backend.api.utils.dependencies import get_database
import os
# import traceback
from typing import Dict # , List
import motor.motor_asyncio
# from utils.json_helper import json_file_builder
from fastapi import HTTPException


MONGO_DETAILS = f"mongodb+srv://{os.getenv("MONGO_USER")}:{os.getenv("MONGO_PASS")}@sports-cluster.mx1mo.mongodb.net/?retryWrites=true&w=majority&appName=Sports-Cluster"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
database = client["sports_data"]
sports_collection = database.get_collection('teams_data')


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
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


async def update_sport(query: Dict, team_name: str, update_data: Dict):
    """
    Updates a specific team in the 'teams' array of a document based on team_name.

    Args:
        query (Dict): The query filter to find the document.
        team_name (str): The name of the team to update.
        update_data (Dict): The fields and values to update for the team.

    Returns:
        str: Message indicating the result of the operation.
    """
    result = await sports_collection.update_one(
        query,
        {
            "$set": {"teams.$[team]": update_data}  # Update the team where the filter matches
        },
        array_filters=[{"team.name": team_name}]  # Using 'team.name' to match the team by name
    )
    
    if result.modified_count > 0:
        return f"Team '{team_name}' was updated."
    return f"No team named '{team_name}' was found or data unchanged."


async def delete_sport(query: Dict, sport_type: str, team_name: str):
    """
    Deletes a specific team from the 'teams' array in the collection based on team_name.

    Args:
        query (Dict): The query filter to find the document.
        team_name (str): The name of the team to remove.

    Returns:
        str: Message indicating the result of the operation.
    """
    # Filter by sport_type and the specific team by name
    result = await sports_collection.update_one(
        {**query, "teams.name": team_name},  # Make sure to filter for the specific team in the sport
        {"$pull": {"teams": {"name": team_name}}}  # Use $pull to remove the team from the teams array
    )
    
    if result.modified_count > 0:
        return f"Team '{team_name}' was removed from the database."
    return f"No team named '{team_name}' was found."
