from typing import Optional
from sqlmodel import SQLModel


class RegionRead(SQLModel):
    id: int
    name: str

class DistrictRead(SQLModel):
    id: int
    region_id: Optional[int] = None
    name: str

class LocalAreaRead(SQLModel):
    id: int
    district_id: Optional[int] = None
    name: str
