#
# main.py
#
# The base route for the FastAPI application.
# Takes in a .csv file and sends the information
# to routers/teams.py
#

import uvicorn
from typing import Dict
from fastapi import FastAPI, Query, UploadFile, File, Depends, Body
from utils.json_helper import json_file_builder
from dependencies import lifespan
from routers.teams import (
    add_sports
)


app = FastAPI(lifespan=lifespan)


# Changed to app.post because this is typically used for
# sending data to the backend, in our case to store the
# data.
@app.post("/")
async def root(
        sport_type: str = Query(...),
        gender: str = Query(...),
        level: str = Query(...),
        csv_file: UploadFile = File(...),
        **algo_values: Dict = Body(...)):
    # Accessing routes via routers/teams.py
    try:
        # This will be going to routers instead

        # # Call the json_file_builder with the query parameters
        # json_structure = json_file_builder(sport_type, gender, level)
        # return json_structure  # Return the structured JSON
    except Exception as e:
        return {"error": str(e)}  # JSON formatted error message


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
