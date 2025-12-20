from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, func
from geoalchemy2 import Geography
from sqlmodel import Column, SQLModel, Field

class Users(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str = Field(max_length=400)
    username: str = Field(max_length=300, nullable=True)
    last_location: Optional[str] = Field(
        default=None,
        sa_column=Column(
            Geography(geometry_type="POINT", srid=4326),
            nullable=True
        )
    )
    local_area_id: int = Field(foreign_key="local_areas.id")
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now()
        )
    )