from typing import Optional
from sqlmodel import SQLModel, Field
from enum import Enum


class LocalAreaType(str, Enum):
    CITY_PART = "city_part"
    VILLAGE = "village"


class LocalAreas(SQLModel, table=True):
    __tablename__ = "local_areas"

    id: Optional[int] = Field(default=None, primary_key=True)
    district_id: int = Field(foreign_key="districts.id")
    name: str = Field(max_length=300)
    type: LocalAreaType = Field(default=LocalAreaType.VILLAGE)
