from datetime import time
import re
from pydantic import field_validator
from sqlmodel import SQLModel, Field
from decimal import Decimal


class StadiumAdminCreate(SQLModel):
    phone: str = Field(
        min_length=7,
        max_length=100,
        description="Telefon raqam"
    )
    stadium_id: int

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
