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
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from dependencies import lifespan
from schemas.items import (
    InputMethod,
    GeneralInputMethod
)
from routers.teams import (
    add_sports,
    list_sports,
    update_teams,
    delete_teams
)


app = FastAPI(lifespan=lifespan)

# CREATE routes:
# Changed to app.post because this is typically used for
# sending data to the backend, in our case to store the
# data.
@app.post("/admin", tags=["Admin"])
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
async def get_sport_categories():
    """
    Retrieves a list of available sport categories and displays them on the homepage.
    """
    try:
        sport_categories = await list_sports()  # TODO: fetch sports categories
        if sport_categories:
            return {
                "message": "Welcome to the Sports API. Here are the available sport categories:",
                "categories": sport_categories
            }
        raise HTTPException(status_code=404, detail="No sport categories found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/sports", tags=["Sports"])
async def get_sports():
    """
    Retrieves a list of all available sports.
    """
    try:
        sports_list = await list_sports() # No parameters: get all sports
        if sports_list:
            return {"message": "Sports data retrieved successfully", "data": sports_list}
        raise HTTPException(status_code=404, detail="No sports data found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/sports/{sport_type}/teams", tags=["Sports"])
async def get_teams(
    sport_type: str
):
    """
    Retrieves a list of all available teams for a given sport.
    """
    try:
        teams_list = await list_sports(sport_type=sport_type)
        if teams_list:
            return {"message": "Teams data retrieved successfully", "data": teams_list}
        raise HTTPException(status_code=404, detail="No teams data found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/sports/{sport_type}/teams/{team_name}", tags=["Sports"])
async def get_team(
    sport_type: str,
    team_name: str,
    input: GeneralInputMethod = Depends()):
    """
    Retrieves team specific data
    (season_opp and eventually prediction info).
    """
    try:
        response = await list_sports(sport_type=sport_type, team_name=team_name, input=input)
        if response:
            return response
        raise HTTPException(status_code=404, detail="No sports data found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# UPDATE routes:
# 7 values passed: 3 up to level, name x2, score x2
@app.put("/admin/{sport_type}/{sport_id}", tags=["Admin"])
async def root(
        sport_type: str,
        sport_id: int,
        input: InputMethod = Depends()):
    try:
        # Call to logic for update_sport_data
        updated_sport = await update_teams
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

# DELETE routes:
# Deletes only season opp array,
# scores, win ratio, win/loss, 
# expected/actual performance,
# and prediction info
@app.delete("/admin/sports/teams/{team_name}", tags=["Admin"])
async def delete_sport(
    team_name: int
    ):
    """
    Deletes a sport by ID.
    - **sport_id**: The ID of the sport to delete.
    """
    try:
        response = await delete_teams(team_name)
        if response:
            return {"message": "Sport deleted successfully"}
        raise HTTPException(status_code=404, detail="Sport not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
