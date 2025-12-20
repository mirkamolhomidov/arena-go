from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, func, Text
from sqlmodel import Column, SQLModel, Field


class StadiumImages(SQLModel, table=True):
    __tablename__ = "stadium_images"

    id: Optional[int] = Field(default=None, primary_key=True)
    stadium_id: int = Field(foreign_key="stadiums.id")
    image_url: str = Field(sa_column=Column(Text, nullable=False))
    main_image: bool = Field(default=False)
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
