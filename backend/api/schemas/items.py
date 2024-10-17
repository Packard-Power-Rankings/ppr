""" items.py

This file defines the Pydantic data model schema
(structure and validation rules for JSON data used to store and retrieve items)
for items in the MongoDB database.

It includes:

- Data field definitions and types.
- Default values and validation constraints.
- Serialization and deserialization logic for integration with MongoDB. 
"""

from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, ValidationError
from config.config import LEVEL_CONSTANTS
from fastapi import Form, Depends, HTTPException


# Enum Definitions (fixed set of values)
class Sport(str, Enum):
    football = "football"
    basketball = "basketball"


class Gender(str, Enum):
    mens = "mens"
    womens = "womens"


class Level(str, Enum):
    college = "college"
    high_school = "high_school"


class InputMethod(BaseModel):
    sport_type: Sport = Field(..., description="Sport Type")
    gender: Gender = Field(..., description="Gender Of Sport")
    level: Level = Field(..., description="Sport Level")
    k_value: Optional[float] = 0.0
    home_advantage: Optional[int] = 0
    average_game_score: Optional[int] = 0
    game_set_len: Optional[int] = 0


async def input_method_dependency(
    sport_type: str = Form(...),
    gender: str = Form(...),
    level: str = Form(...),
    k_value: Optional[float] = Form(0.0),
    home_advantage: Optional[int] = Form(0),
    average_game_score: Optional[int] = Form(0),
    game_set_len: Optional[int] = Form(0),
) -> InputMethod:
    # Convert form inputs to the expected enum types
    try:
        return InputMethod(
            sport_type=Sport(sport_type),
            gender=Gender(gender),
            level=Level(level),
            k_value=k_value,
            home_advantage=home_advantage,
            average_game_score=average_game_score,
            game_set_len=game_set_len
        )
    except (ValueError, ValidationError) as e:
        raise HTTPException(status_code=422, detail=f"Invalid input: {str(e)}")


class GeneralInputMethod(BaseModel):
    # sport_type: Sport = Field(..., description="Type of Sport")
    gender: Gender = Field(..., description="Gender Of Sport")
    level: Level = Field(..., description="Sport Level")


class SeasonOpponent(BaseModel):
    id: int = Field(..., description="Opponent ID")
    home_game_bool: bool = Field(..., description="Is the game a home game")
    home_score: int = Field(..., description="Home team score")
    away_score: int = Field(..., description="Away team score")
    power_difference: float = Field(
        ..., description="Difference in team power rankings"
    )
    home_zscore: float = Field(..., description="Home team Z-score")
    away_zscore: float = Field(..., description="Away team Z-score")
    date: str = Field(
        ..., pattern=r'^\d{2}/\d{2}/\d{4}$',
        description="Match date in mm/dd/yyyy format"
    )


class PredictionInfo(BaseModel):
    expected_performance: float = Field(
        ..., description="Expected performance metrics"
    )
    actual_performance: float = Field(
        ..., description="Actual performance metrics"
    )
    predicted_score: float = Field(
        ..., description="Predicted score for the game"
    )


class Team(BaseModel):
    id: int = Field(..., description="Team ID") # class-ified
    team_name: str = Field(..., description="Name of the team")
    city: Optional[str] = Field(None, description="Team's city")
    state: Optional[str] = Field(None, description="Team's state")
    power_ranking: float = Field(..., description="Power ranking for the team")
    win_ratio: float = Field(..., description="Win ratio for the team")
    date: str = Field(
        ..., pattern=r'^\d{2}/\d{2}/\d{4}$',
        description="Match date in mm/dd/yyyy format"
    )
    season_opp: List[SeasonOpponent] = Field(
        ..., description="List of team opponents"
    )
    prediction_info: List[PredictionInfo] = Field(
        ..., description="List of predicted and actual performance metrics")


class LevelData(BaseModel):
    k_value: float = Field(..., description="K-factor used in rankings")
    home_advantage: int = Field(..., description="Home advantage points")
    average_game_score: int = Field(..., description="Average game score")
    game_set_len: int = Field(..., description="Length of the game set")
    team: List[Team] = Field(..., description="Team information")


class GenderData(BaseModel):
    men: LevelData = Field(..., description="Men's sports data")
    women: LevelData = Field(..., description="Women's sports data")


class TeamData(BaseModel):
    id: int
    team_name: str
    city: Optional[str]
    state: Optional[str]
    wins: int
    losses: int
    z_score: float
    power_ranking: float
    season_opp: List[Dict]
    prediction_info: List[Dict[str, float]]


class OpponentData(BaseModel):
    id: int
    home_game_bool: bool
    home_score: int
    away_score: int
    power_difference: float
    home_zscore: float
    away_zscore: float
    date: Optional[int]


def ResponseModel(data, message):
    return {
        'data': [data],
        'code': 200,
        'message': message,
    }
