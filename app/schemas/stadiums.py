from datetime import time
import re
from pydantic import field_validator
from sqlmodel import SQLModel, Field
from decimal import Decimal


class StadiumCreate(SQLModel):
    name: str = Field(
        min_length=3,
        max_length=400,
        description="Stadion nomi"
    )
    address: str = Field(
        min_length=5,
        description="Manzil"
    )
    phone: str = Field(
        min_length=7,
        max_length=100,
        description="Telefon raqam"
    )
    start_time: time
    end_time: time
    price_per_hour: Decimal = Field(
        ge=0,
        description="Soatlik narx"
    )
    local_area_id: int = Field(
        gt=0,
        description="Local area ID"
    )
    lat: float
    long: float

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str):
        if len(v) < 3:
            raise ValueError("Stadion nomi kamida 3 ta belgidan iborat bo'lishi kerak")
        elif len(v) > 400:
            raise ValueError("Stadion nomi 400 ta belgidan kam bo'lishi kerak")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str):
            uzb_phone_regex = r"^(998)?(33|88|90|91|93|94|95|97|98|99)\d{7}$"
            v = v.replace(" ", "").replace("-", "").replace("+", "")

            if not re.match(uzb_phone_regex, v):
                raise ValueError(
                    "Telefon raqami noto'g'ri formatda. "
                    "Namuna: 998901234567 yoki 901234567"
                )
            return v
