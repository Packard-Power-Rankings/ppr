# 
# dependencies.py
#
# The main entry point for running the FastAPI applicaton
# via Uvicorn server.
#

from fastapi import FastAPI
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mongodb_client = AsyncIOMotorClient("mongodb://localhost:27017")
    app.mongodb = app.mongodb_client["PPR-DB"]
    yield
    app.mongodb_client.close()
