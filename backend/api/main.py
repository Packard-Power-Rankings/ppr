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
    # GeneralInputMethod,
    input_method_dependency
)
from routers.teams import (
    add_sports,
    list_teams,
    list_teams_info,
    update_teams,
    delete_teams
)
from fastapi.middleware.cors import CORSMiddleware
from schemas import items


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
        input: InputMethod = Depends(input_method_dependency),
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
# These GET routes will handle requests made to the given URL.
# The next step is going to routers.
@app.get("/{sport_type}/", tags=["Sports"])
async def get_teams(
    sport_type: str,
    search_params: items.GeneralInputMethod = Depends()
):
    """
    Retrieves a list of all available teams for a given sport.
    """
    try:
        teams_list = await list_teams(
            sport_type=sport_type,
            search_params=search_params
        )
        if teams_list:
            return {"message": "Teams data retrieved successfully", "data": teams_list}
        raise HTTPException(status_code=404, detail="No teams data found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/{sport_type}/{team_name}/", tags=["Sports"])
async def get_team(
    sport_type: str,
    team_name: str,
    search_params: items.GeneralInputMethod = Depends()
):
    """
    Retrieves team specific data
    (season_opp and eventually prediction info).
    """
    try:
        teams_info_list = await list_teams_info(
            sport_type=sport_type,
            team_name=team_name,
            search_params=search_params)
        if teams_info_list:
            return teams_info_list
        raise HTTPException(status_code=404, detail="No sports data found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# UPDATE routes:
# 7 values passed: 3 up to level, name x2, score x2
@app.put("/admin/{sport_type}/{team_name}", tags=["Admin"])
async def root(
        sport_type: str,
        team_name: str,
        search_params: items.GeneralInputMethod = Depends()):
    try:
        # Call to logic for update_sport_data
        updated_sport = await update_teams
        # Calls to various functions from routers/teams.py
        # to validate and process CSV data.
        response = await update_teams(
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
@app.delete("/admin/{sport_type}/{team_name}", tags=["Admin"])
async def delete_sport(
    sport_type: str,
    team_name: str
    ):
    """
    Deletes a sport by name.
    
    Args:
        sport_type (str): The type of sport (e.g., basketball, football).
        team_name (str): The name of the team to delete.

    Returns:
        JSON response indicating success or failure.
    """
    try:
        # Call the delete_teams function to delete the specific team's data
        response = await delete_teams(sport_type, team_name)
        
        # Assuming delete_teams returns a message string
        return {"message": response}  # Return the message from delete_teams
        
    except HTTPException as http_exc:
        raise http_exc  # Re-raise known HTTP exceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
