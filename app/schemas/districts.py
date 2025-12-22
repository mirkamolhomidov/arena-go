from typing import Optional
from sqlmodel import SQLModel
from enum import Enum


class DistrictRead(SQLModel):
    id: int
    region_id: Optional[int] = None
    name: str
