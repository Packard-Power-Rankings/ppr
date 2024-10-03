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
from fastapi import FastAPI, UploadFile, File, Depends
from dependencies import lifespan
from schemas.items import InputMethod
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
@app.post("/admin/", tags=["Sports"])
async def root(
        input: InputMethod = Depends(),
        csv_file: UploadFile = File(...)):
    try:
        # Ensure the file type is correct
        if not csv_file.filename.endswith('.csv'):
            return {"error": "File must be a CSV."}
        algo_values = input.model_dump(
            exclude=("sport_type", "gender", "level")
        )
        # Calls to various functions from routers/teams.py
        # to validate and process CSV data.
        response = await add_sports(
            input.sport_type,
            input.gender,
            input.level,
            csv_file,
            **algo_values
        )

        return response
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
