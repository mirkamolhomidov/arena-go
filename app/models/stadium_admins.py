from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, func, Text
from sqlmodel import Column, SQLModel, Field


class StadiumAdmins(SQLModel, table=True):
    __tablename__ = "stadium_admins"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    stadium_id: int = Field(foreign_key="stadiums.id")
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
