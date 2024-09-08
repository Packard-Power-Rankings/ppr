"""File to define the structure of the JSON format for storing
and retrieving data
"""

from typing import List, Optional, Any, Generator
from datetime import date
from enum import Enum
from bson import ObjectId
from pydantic import BaseModel, Field


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


class Level(str, Enum):
    HIGH_SCHOOL = "high_school"
    COLLEGE = "college"


class Gender(str, Enum):
    MENS = "mens"
    WOMENS = "womens"


class Football(BaseModel):
    id: PydanticObjectId = Field(
        default_factory=PydanticObjectId,
        alias='id'
    )
    level: Level


class BasketBall(BaseModel):
    id: PydanticObjectId = Field(
        default_factory=PydanticObjectId,
        alias='id'
    )
    level: Level
    gender: Optional[Gender]
