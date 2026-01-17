from datetime import time
import re
from pydantic import field_validator
from sqlmodel import SQLModel, Field


class UserCreate(SQLModel):
    first_name: str = Field(
        min_length=1,
        max_length=400,
        description="Foydalanuvchi ismi"
    )
    username: str = Field(
        max_length=70,
        description="Foydalanuvchi nomi"
    )
    phone: str = Field(
        min_length=7,
        max_length=100,
        description="Telefon raqam"
    )
    telegram_id: int = Field(
        gt=0,
        description="Telegram foydalanuvchi ID"
    )
    local_area_id: int = Field(
        gt=0,
        description="Local area ID"
    )
    @field_validator("first_name")
    @classmethod
    def validate_name(cls, v: str):
        if len(v) < 1:
            raise ValueError("Foydalanuvchi ismi kamida 1 ta belgidan iborat bo'lishi kerak")
        elif len(v) > 400:
            raise ValueError("Foydalanuvchi ismi 400 ta belgidan kam bo'lishi kerak")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str):
            uzb_phone_regex = r"^(998)?(77|33|88|90|91|93|94|95|97|98|99)\d{7}$"
            v = v.replace(" ", "").replace("-", "").replace("+", "")

            if not re.match(uzb_phone_regex, v):
                raise ValueError(
                    "Telefon raqami noto'g'ri formatda. "
                    "Namuna: 998901234567 yoki 901234567"
                )
            return v
