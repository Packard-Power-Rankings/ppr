# 
# dependencies.py
#
# The main entry point for running the FastAPI applicaton
# via Uvicorn server.
#

from fastapi import FastAPI
from contextlib import asynccontextmanager

from api.database import mongo_client, sports_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mongodb_client = mongo_client
    app.mongodb = sports_database
    yield
