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
from fastapi import FastAPI, UploadFile, File, Depends, Query
from dependencies import lifespan
from schemas.items import (
    InputMethod,
    GeneralInputMethod
)
from routers.teams import (
    add_sports,
    list_sports
)
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(lifespan=lifespan)

# Add CORS middleware to allow requests from React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CREATE routes:
# Changed to app.post because this is typically used for
# sending data to the backend, in our case to store the
# data.


@app.post("/admin/", tags=["Admin"])
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


# READ routes:
# Browsers only allow GET requests when you navigate to a URL.
# This GET route will handle requests made to the root URL.
# The next step is going to routers.
@app.get("/", tags=["Sports"])
async def read_root():
    return {"message:" "Welcome page:"}


@app.get("/sports/", tags=["Sports"])
async def read_root():
    return {"message": "Sports navigation:"}


@app.get("/sports/teams", tags=["Sports"])
async def read_root():
    return {"message": "Teams navigation:"}


@app.get("/sports/teams/{team_id}", tags=["Sports"])
async def get_team(
        team_id: int,
        input: GeneralInputMethod = Depends()):
    try:
        response = await list_sports(team_id, input)
        if response:
            return response
        else:
            return {"message": "No sports data found"}
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

# # UPDATE routes:
# @app.put("/admin/sports/{sport_id}", tags=["Sports"])
# async def root(
#         sport_id: int,
#         input: InputMethod = Depends()):
#     try:
#         # Call to logic for update_sport_data
#         updated_sport = await
#         # Calls to various functions from routers/teams.py
#         # to validate and process CSV data.
#         response = await add_sports(
#             input.sport_type,
#             input.gender,
#             input.level,
#             csv_file,
#             **algo_values
#         )

#         return response
#     except Exception as e:
#         return {"error": f"An error occurred: {str(e)}"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
