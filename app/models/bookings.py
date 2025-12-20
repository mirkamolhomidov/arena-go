from datetime import date, time
from typing import Optional
from sqlalchemy import BigInteger
from sqlmodel import Column, SQLModel, Field
from enum import Enum

class BookingStatus(str, Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"

class Bookings(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    stadium_id: int = Field(foreign_key="stadiums.id")
    user_telegram_id: int = Field(
        sa_column=Column(BigInteger(), index=True, nullable=False)
    )
    booking_date: date = Field(nullable=False)
    start_time: time = Field(nullable=False)
    end_time: time = Field(nullable=False)
    status: BookingStatus = Field(default=BookingStatus.CONFIRMED)
