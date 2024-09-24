# 
# dependencies.py
#
# The base route for the FastAPI application.
#

from fastapi import FastAPI, Query
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from utils.json_helper import json_file_builder

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mongodb_client = AsyncIOMotorClient("mongodb://localhost:27017")
    app.mongodb = app.mongodb_client["PPR-DB"]
    yield
    app.mongodb_client.close()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root(sport_type: str = Query(...), gender: str = Query(...), level: str = Query(...)):
    try:
        # Call the json_file_builder with the query parameters
        json_structure = json_file_builder(sport_type, gender, level)
        return json_structure  # Return the structured JSON
    except Exception as e:
        return {"error": str(e)}  # JSON formatted error message
        