import re
from decimal import Decimal

from pydantic import field_validator
from sqlmodel import Field, SQLModel


ALLOWED_FIELD_SIZES = {"5x5", "6x6", "7x7"}


class StadiumCreate(SQLModel):
    name: str = Field(
        min_length=3,
        max_length=400,
        description="Stadion nomi",
    )
    address: str = Field(
        min_length=5,
        description="Manzil",
    )
    phone: str = Field(
        min_length=7,
        max_length=100,
        description="Telefon raqam",
    )
    field_size: str = Field(description="Maydon o'lchami")
    condition_score: int = Field(
        ge=0,
        le=10,
        description="Stadion holati 0 dan 10 gacha",
    )
    amenities: str = Field(
        min_length=1,
        max_length=1000,
        description="Qulayliklar va sharoitlar haqida info",
    )
    price_per_hour: Decimal = Field(
        ge=0,
        description="Soatlik narx",
    )
    local_area_id: int = Field(
        gt=0,
        description="Local area ID",
    )
    lat: float
    long: float

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str):
        if len(v) < 3:
            raise ValueError("Stadion nomi kamida 3 ta belgidan iborat bo'lishi kerak")
        if len(v) > 400:
            raise ValueError("Stadion nomi 400 ta belgidan kam bo'lishi kerak")
        return v.strip()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str):
        uzb_phone_regex = r"^(998)?(33|88|90|91|93|94|95|97|98|99)\d{7}$"
        normalized = v.replace(" ", "").replace("-", "").replace("+", "")

        if not re.match(uzb_phone_regex, normalized):
            raise ValueError(
                "Telefon raqami noto'g'ri formatda. "
                "Namuna: 998901234567 yoki 901234567"
            )
        return normalized

    @field_validator("field_size", mode="before")
    @classmethod
    def validate_field_size(cls, v):
        if not isinstance(v, str):
            raise ValueError("Maydon o'lchamini tanlang")

        normalized = v.strip().lower().replace("×", "x").replace(" ", "")
        if normalized not in ALLOWED_FIELD_SIZES:
            raise ValueError("Maydon o'lchami faqat 5x5, 6x6 yoki 7x7 bo'lishi mumkin")
        return normalized

    @field_validator("amenities")
    @classmethod
    def validate_amenities(cls, v: str):
        normalized = v.strip()
        if not normalized:
            raise ValueError("Qulayliklar haqida kamida qisqa info kiriting")
        return normalized
