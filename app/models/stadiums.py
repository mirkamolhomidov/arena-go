from datetime import datetime
from decimal import Decimal
from typing import Optional

from geoalchemy2 import Geography
from sqlalchemy import DateTime, Integer, Numeric, String, Text, func
from sqlmodel import Column, Field, SQLModel


class Stadiums(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=400)
    address: str = Field(sa_column=Column(Text, nullable=False))
    phone: str = Field(max_length=100)
    price_per_hour: Decimal = Field(
        sa_column=Column(Numeric(precision=12, scale=2), default=0.00)
    )
    field_size: Optional[str] = Field(
        default=None,
        sa_column=Column(String(length=10), nullable=True),
    )
    condition_score: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, nullable=True),
    )
    amenities: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    location: Optional[str] = Field(
        default=None,
        sa_column=Column(
            Geography(geometry_type="POINT", srid=4326),
            nullable=True,
        ),
    )
    local_area_id: int = Field(foreign_key="local_areas.id")
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
        )
    )
