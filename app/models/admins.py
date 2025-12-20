from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, func, BigInteger
from sqlmodel import Column, SQLModel, Field
from enum import Enum


class AdminPosition(str, Enum):
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


class Admins(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str = Field(max_length=400)
    username: str = Field(max_length=300)
    phone: str = Field(max_length=100)
    stadium_id: int = Field(foreign_key="stadiums.id")
    telegram_id: int = Field(
        sa_column=Column(BigInteger(), index=True, nullable=False)
    )
    position: AdminPosition = Field(default=AdminPosition.ADMIN)
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
