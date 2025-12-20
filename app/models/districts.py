from typing import Optional
from sqlmodel import SQLModel, Field
from enum import Enum

class DistrictType(str, Enum):
    CITY = "city"
    DISTRICT = "district"

class Districts(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    region_id: int = Field(foreign_key="regions.id")
    name: str = Field(max_length=100)
    type: DistrictType = Field(default=DistrictType.DISTRICT)
