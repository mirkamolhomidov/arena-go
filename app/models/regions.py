from typing import Optional
from sqlmodel import SQLModel, Field


class Regions(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
