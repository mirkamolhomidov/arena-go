from datetime import date, time
from enum import Enum
from typing import Optional

from sqlalchemy import BigInteger, Column, Enum as SAEnum
from sqlmodel import Field, SQLModel


class BookingStatus(str, Enum):
    PENDING = "pending"
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
    status: BookingStatus = Field(
        default=BookingStatus.PENDING,
        sa_column=Column(
            SAEnum(BookingStatus, name="bookingstatus"),
            nullable=False,
            server_default=BookingStatus.PENDING.name,
        ),
    )
