import os
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Any

from api.database import mongo_client


DB_NAME = os.getenv("MONGO_DB_NAME", "Unrecognized")


def get_mongo_client() -> AsyncIOMotorClient:
    return mongo_client


def get_database(db_name: str = DB_NAME) -> Any:
    client = get_mongo_client()
    return client[db_name]
