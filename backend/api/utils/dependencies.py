import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from typing import Any


DB_NAME = os.getenv("MONGO_DB_NAME", "Unrecognized")


def get_mongo_client() -> AsyncIOMotorClient:
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    return client


def get_database(db_name: str = DB_NAME) -> Any:
    client = get_mongo_client()
    return client[db_name]
