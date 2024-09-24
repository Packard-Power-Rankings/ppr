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

from typing import List, Optional, Any, Generator, Dict, Tuple
from datetime import date
from enum import Enum
from bson import ObjectId
from pydantic import BaseModel, Field
from api.config import LEVEL_CONSTANTS

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

class SportType(str, Enum):
    FOOTBALL = "football"
    BASKETBALL = "basketball"


class Gender(str, Enum):
    MENS = "mens"
    WOMENS = "womens"


class Level(str, Enum):
    HIGH_SCHOOL = "high_school"
    COLLEGE = "college"


class Sport(BaseModel):
    sport_type: SportType


class GenderType(BaseModel):
    gender: Gender


class LevelType(BaseModel):
    level: Level


class AlgoValues(BaseModel):
    k_value: float = Field(0.0)
    home_advantage: int = Field(0)
    average_game_score: int = Field(0)
    game_set_len: int = Field(0)

    @classmethod
    def constant_finder(
            cls,
            sport_type: SportType,
            gender: Gender,
            level: Level):
        lvl_key = (sport_type.value, gender.value, level.value)
        if lvl_key in LEVEL_CONSTANTS[lvl_key]:
            return cls(**LEVEL_CONSTANTS[lvl_key])
        return cls()


class TeamData(BaseModel):
    id: int
    team: str
    city: Optional[str]
    state: Optional[str]
    conference: str
    division: str
    wins: int
    losses: int
    z_score: float
    power_ranking: float
    season_opp: List[Dict]


class OpponentData(BaseModel):
    id: int
    date: Optional[int]
