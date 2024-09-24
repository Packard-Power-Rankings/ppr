"""Defines the Pydantic data model schema for items in the MongoDB database.

This file outlines the structure and validation rules for JSON data used
to store and retrieve items. It includes:

- Data field definitions and types.
- Default values and validation constraints.
- Handling of MongoDB-specific types (e.g., ObjectId).
- Serialization and deserialization logic for integration with MongoDB.

The schema ensures that all data adheres to the specified format and
constraints, enabling consistent and reliable data handling
within the application.
"""

from pydantic import BaseModel, Field
from typing import List

class SeasonOpponent(BaseModel):
    opp_id: int = Field(..., description="Opponent ID")
    date: str = Field(..., description="Game date")

class Team(BaseModel):
    id: int = Field(..., description="Team ID")
    city: str = Field(..., description="Team's city")
    state: str = Field(..., description="Team's state")
    conference: str = Field(..., description="Team's conference")
    division: str = Field(..., description="Team's division")
    score: int = Field(..., description="Team's score")
    z_score: float = Field(..., description="Z-score for the team")
    power_ranking: float = Field(..., description="Power ranking for the team")
    season_opp: List[SeasonOpponent] = Field(..., description="List of team opponents")

class LevelData(BaseModel):
    k_value: float = Field(..., description="K-factor used in rankings")
    home_advantage: int = Field(..., description="Home advantage points")
    average_game_score: int = Field(..., description="Average game score")
    game_set_len: int = Field(..., description="Length of the game set")
    team: List[Team] = Field(..., description="Team information")

class GenderData(BaseModel):
    men: LevelData = Field(..., description="Men's sports data")
    women: LevelData = Field(..., description="Women's sports data")

class Sport(BaseModel):
    gender: GenderData = Field(..., description="Sports data for gender")

class SportsSchema(BaseModel):
    sports: dict[str, Sport] = Field(..., description="Dictionary containing all sports data")
