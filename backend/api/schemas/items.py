"""File to define the structure of the JSON format for storing
and retrieving data
"""

from typing import List, Optional, Any, Generator, Dict, Tuple
from datetime import date
from enum import Enum
from bson import ObjectId
from pydantic import BaseModel, Field
from api.config import LEVEL_CONSTANTS


class PydanticObjectId(ObjectId):
    @classmethod
    def __get_validator__(cls) -> Generator:
        yield cls.validate

    @classmethod
    def validate(cls, v) -> ObjectId:
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema) -> None:
        field_schema.update(type='string')


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
