#
# main.py
#
# The base route for the FastAPI application.
# Takes in a .csv file and sends the information
# to routers/teams.py
#

import uvicorn
from fastapi import FastAPI, Query
from utils.json_helper import json_file_builder
from dependencies import lifespan

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root(sport_type: str = Query(...), gender: str = Query(...), level: str = Query(...)):
    # Accessing routes via routers/teams.py
    try:
        # Call the json_file_builder with the query parameters
        json_structure = json_file_builder(sport_type, gender, level)
        return json_structure  # Return the structured JSON
    except Exception as e:
        return {"error": str(e)}  # JSON formatted error message

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
