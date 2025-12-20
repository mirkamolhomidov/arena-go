from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import DateTime, Text, func, Numeric
from geoalchemy2 import Geography
from sqlmodel import Column, SQLModel, Field
from enum import Enum


class StadiumStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


class Stadiums(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=400)
    address: str = Field(sa_column=Column(Text, nullable=False))
    phone: str = Field(max_length=100)
    working_time: str = Field(max_length=200)
    price_per_hour: Decimal = Field(
        sa_column=Column(Numeric(precision=12, scale=2), default=0.00)
    )
    status: StadiumStatus = Field(default=StadiumStatus.OPEN)
    location: Optional[str] = Field(
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
