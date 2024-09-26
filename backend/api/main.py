#
# main.py
#
# The base route for the FastAPI application.
#
# Takes in a .csv file and sends it to routers/teams.py
# that parses it to JSON.
#

import uvicorn
from typing import Dict
from fastapi import FastAPI, UploadFile, File, Body
from dependencies import lifespan
from routers.teams import (
    add_sports
)


app = FastAPI(lifespan=lifespan)

# Browsers only allow GET requests when you navigate to a URL.
# This GET route will handle requests made to the root URL.
@app.get("/")
async def read_root():
    return {"message": "Welcome to the Sports API!"}

# Changed to app.post because this is typically used for
# sending data to the backend, in our case to store the
# data.
@app.post("/")
async def root(
        sport_type: str = Body(...),
        gender: str = Body(...),
        level: str = Body(...),
        csv_file: UploadFile = File(...),
        **algo_values: Dict):
    try:
        # Ensure the file type is correct
        if not csv_file.filename.endswith('.csv'):
            return {"error": "File must be a CSV."}

        # Calls to various functions from routers/teams.py
        # to validate and process CSV data.
        response = await add_sports(csv_file, sport_type, gender, level, **algo_values)

        return response
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
