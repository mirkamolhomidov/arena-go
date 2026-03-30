from datetime import date, datetime, time
from typing import Optional

from pydantic import model_validator, field_validator
from sqlmodel import Field, SQLModel

from app.models.bookings import BookingStatus


class BookingCreate(SQLModel):
    stadium_id: int = Field(gt=0, description="Stadion ID")
    user_telegram_id: int = Field(gt=0)

    booking_date: date
    start_time: time
    end_time: time

    status: Optional[BookingStatus] = BookingStatus.CONFIRMED

    @field_validator("booking_date", mode="before")
    @classmethod
    def parse_booking_date(cls, v):
        if isinstance(v, date) and not isinstance(v, datetime):
            return v

        if isinstance(v, str):
            try:
                return datetime.strptime(v, "%Y-%m-%d").date()
            except ValueError as exc:
                raise ValueError(
                    "Band qilish sanasi noto'g'ri. To'g'ri format: 2026-01-02"
                ) from exc

        raise ValueError("Band qilish sanasi noto'g'ri")

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def parse_booking_time(cls, v):
        if isinstance(v, time):
            return v

        if isinstance(v, str):
            try:
                return datetime.strptime(v, "%H:%M").time()
            except ValueError as exc:
                raise ValueError(
                    "Vaqt noto'g'ri. To'g'ri format: 09:30"
                ) from exc

        raise ValueError("Vaqt noto'g'ri")

    @model_validator(mode="after")
    def validate_booking(self):
        if self.booking_date < date.today():
            raise ValueError("O'tgan sanaga band qilish mumkin emas")

        if self.start_time >= self.end_time:
            raise ValueError("Boshlanish vaqti tugash vaqtidan oldin bo'lishi kerak")

        return self
