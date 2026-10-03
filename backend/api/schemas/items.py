""" items.py

This file defines the Pydantic data model schema
(structure and validation rules for JSON data used to store and retrieve items)
for items in the MongoDB database.

It includes:

- Data field definitions and types.
- Default values and validation constraints.
- Serialization and deserialization logic for integration with MongoDB. 
"""

from typing import List, Optional, Dict, Literal
import json
from enum import Enum
from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    field_validator,
    model_validator
)
# from config.constants import LEVEL_CONSTANTS
from fastapi import Form, HTTPException, UploadFile


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


async def input_method_dependency(
    sport_type: Sport = Form(...),
    gender: Gender = Form(...),
    level: Level = Form(...),
) -> InputMethod:
    # Convert form inputs to the expected enum types
    try:
        return InputMethod(
            sport_type=Sport(sport_type),
            gender=Gender(gender),
            level=Level(level),
        )
    except (ValueError, ValidationError) as e:
        raise HTTPException(status_code=422, detail=f"Invalid input: {str(e)}")


class GeneralInputMethod(BaseModel):
    sport_type: Sport = Field(..., description="Type of Sport")
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


# class PredictionInfo(BaseModel):
#     expected_performance: float = Field(
#         ..., description="Expected performance metrics"
#     )
#     actual_performance: float = Field(
#         ..., description="Actual performance metrics"
#     )
#     predicted_score: float = Field(
#         ..., description="Predicted score for the game"
#     )


class Team(BaseModel):
    id: int = Field(..., description="Team ID")  # class-ified
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
    # prediction_info: List[PredictionInfo] = Field(
    #     ..., description="List of predicted and actual performance metrics")


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
    # prediction_info: List[Dict[str, float]]


class OpponentData(BaseModel):
    id: int
    home_game_bool: bool
    home_score: int
    away_score: int
    power_difference: float
    home_zscore: float
    away_zscore: float
    date: Optional[int]


class UpdateTeamsData(BaseModel):
    date: str = Field(..., description="Week Played")
    game_id: Optional[str] = Field(default=None, description="Stored Game ID")
    home_team: str = Field(..., description="Home Team Name")
    away_team: str = Field(..., description="Away Team Name")
    home_score: int = Field(..., description="Home Team Score")
    away_score: int = Field(..., description="Away Team Score")


class UpdateTeamInfo(BaseModel):
    short_name: str = Field(..., min_length=1, max_length=150)
    long_name: str = Field(default="", max_length=200)
    state: str = Field(default="", max_length=50)
    division: str = Field(default="", max_length=100)
    conference: str = Field(default="", max_length=150)
    ranked: bool

    @field_validator("short_name", "long_name", "state", "division", "conference")
    @classmethod
    def strip_team_text(cls, value: str) -> str:
        return " ".join(value.split())


class NewGameData(BaseModel):
    """One game submitted through the admin Add Games form."""

    date: str = Field(..., min_length=1, max_length=10)
    home_team: str = Field(..., min_length=1, max_length=200)
    away_team: str = Field(..., min_length=1, max_length=200)
    home_score: int = Field(..., ge=0)
    away_score: int = Field(..., ge=0)
    neutral_site: Literal[0, 999] = 0

    @field_validator("date", "home_team", "away_team")
    @classmethod
    def strip_game_text(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("value cannot be blank")
        return value

    @model_validator(mode="after")
    def teams_must_be_different(self):
        if self.home_team.casefold() == self.away_team.casefold():
            raise ValueError("home_team and away_team must be different")
        return self


async def update_method(
    date: str = Form(...),
    game_id: Optional[str] = Form(default=None),
    home_team: str = Form(...),
    away_team: str = Form(...),
    home_score: int = Form(...),
    away_score: int = Form(...)
) -> UpdateTeamsData:
    # Convert form inputs to the expected enum types
    try:
        return UpdateTeamsData(
            date=date,
            game_id=game_id,
            home_team=home_team,
            away_team=away_team,
            home_score=home_score,
            away_score=away_score
        )
    except (ValueError, ValidationError) as e:
        raise HTTPException(status_code=422, detail=f"Invalid input: {str(e)}")


class UpdateRequest(BaseModel):
    added_teams: List[Team]


class TokenData(BaseModel):
    username: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str


class LogoutResponse(BaseModel):
    message: str


class SetupAdminRequest(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=64,
        pattern=r"^[A-Za-z0-9_.-]+$",
    )
    password: str = Field(..., min_length=12, max_length=72)

    @field_validator("username", "password")
    @classmethod
    def strip_admin_credentials(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value cannot be blank")
        return value

    @field_validator("password")
    @classmethod
    def enforce_bcrypt_byte_limit(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("password cannot exceed 72 UTF-8 bytes")
        return value


class FlaggedGame(BaseModel):
    game_id: str = Field(..., min_length=1, max_length=200)
    team1_id: int = Field(..., gt=0)
    team1_name: str = Field(..., min_length=1, max_length=200)
    team2_id: int = Field(..., gt=0)
    team2_name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=5, max_length=1000)

    @field_validator("game_id", "team1_name", "team2_name")
    @classmethod
    def strip_flagged_game_text(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("description")
    @classmethod
    def strip_issue_description(cls, value: str) -> str:
        description = value.strip()
        if len(description) < 5:
            raise ValueError("description must contain at least 5 characters")
        return description

    @model_validator(mode="after")
    def teams_must_be_different(self):
        if self.team1_id == self.team2_id:
            raise ValueError("flagged game teams must be different")
        return self


class NewTeamData(BaseModel):
    team_id: int = Field(..., gt=0)
    short_name: str = Field(..., min_length=1, max_length=150)
    long_name: str = Field(default="", max_length=200)
    state: str = Field(default="", max_length=50)
    division: str = Field(default="", max_length=100)
    conference: str = Field(default="", max_length=150)
    ranked: bool = False
    power_ranking: float = 0.0

    @field_validator("short_name", "long_name", "state", "division", "conference")
    @classmethod
    def strip_new_team_text(cls, value: str) -> str:
        return " ".join(value.split())


class NewTeamList(BaseModel):
    teams: Optional[List[NewTeamData]] = Field(default=List)

    @model_validator(mode='before')
    @classmethod
    def parse_teams(cls, values):
        if isinstance(values, str):
            values = json.loads(values)
        return values


def ResponseModel(data, num_of_files, message):
    return {
        'data': data,
        'files_uploaded': num_of_files,
        'code': 200,
        'message': message,
    }
