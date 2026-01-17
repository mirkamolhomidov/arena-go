from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, DateTime, func
from geoalchemy2 import Geography
from sqlmodel import Column, SQLModel, Field
import enum
from sqlalchemy import Enum as SAEnum

class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"
    superadmin = "superadmin"

class Users(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str = Field(max_length=400)
    username: str = Field(max_length=300, nullable=True)
    phone: str = Field(
        min_length=6,
        max_length=50,
    )
    telegram_id: int = Field(
        sa_column=Column(
            BigInteger,
            unique=True,
            nullable=False,
            index=True
        )
    )
    local_area_id: int = Field(foreign_key="local_areas.id")
    role: UserRole = Field(
        sa_column=Column(
            SAEnum(UserRole, name="user_role_enum"),
            nullable=False,
            server_default="user"
        )
    )
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