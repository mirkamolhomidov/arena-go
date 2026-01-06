from datetime import date, datetime
from typing import Optional

from pydantic import model_validator, field_validator
from sqlmodel import Field, SQLModel

from app.models.bookings import BookingStatus


class BookingCreate(SQLModel):
    stadium_id: int = Field(description="Stadion ID")
    user_telegram_id: int

    booking_date: str
    start_time: str
    end_time: str

    status: Optional[BookingStatus] = BookingStatus.CONFIRMED

    @model_validator(mode="before")
    @classmethod
    def validate_formats(cls, data: dict):
        errors = []

        if "booking_date" in data:
            try:
                datetime.strptime(data["booking_date"], "%Y-%m-%d")
            except Exception:
                errors.append("Band qilish sanasi noto'g'ri. To'g'ri format: 2026-01-02")

        if "start_time" in data:
            try:
                datetime.strptime(data["start_time"], "%H:%M")
            except Exception:
                errors.append("Boshlash vaqti noto'g'ri. To'g'ri format: 09:30")

        if "end_time" in data:
            try:
                datetime.strptime(data["end_time"], "%H:%M")
            except Exception:
                errors.append("Tugash vaqti noto'g'ri. To'g'ri format: 23:45")

        if errors:
            raise ValueError(" | ".join(errors))

        return data

    @field_validator("booking_date")
    @classmethod
    def check_not_past(cls, v: str):
        parsed_date = datetime.strptime(v, "%Y-%m-%d").date()
        if parsed_date < date.today():
            raise ValueError("O'tgan sanaga band qilish mumkin emas")
        return v
