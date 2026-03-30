import httpx
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from app.core.config import settings


ADMIN_ROLES = {"admin", "superadmin"}


def get_main_menu(role: str = "user"):
    """Asosiy menyu klaviaturasi"""
    keyboard_rows = [
        [
            KeyboardButton(text="📍 Stadion topish"),
            KeyboardButton(text="🏘 Hududimdagi stadionlar"),
        ],
        [
            KeyboardButton(text="📅 Mening bronlarim"),
            KeyboardButton(text="⚙️ Sozlamalar"),
        ],
    ]

    if role in ADMIN_ROLES:
        keyboard_rows.append([KeyboardButton(text="🛠 Admin panel")])

    keyboard = ReplyKeyboardMarkup(
        keyboard=keyboard_rows,
        resize_keyboard=True,
        input_field_placeholder="Tanlang..."
    )
    return keyboard


async def get_main_menu_for_user(telegram_id: int) -> ReplyKeyboardMarkup:
    role = "user"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.BASE_URL}/users/{telegram_id}",
                timeout=15.0,
            )

        if response.status_code == 200:
            role = response.json().get("role", "user")
    except httpx.HTTPError:
        role = "user"

    return get_main_menu(role)


def get_location_request_keyboard():
    """Lokatsiya so'rash klaviaturasi"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📍 Lokatsiyamni yuborish",
                               request_location=True)
            ],
            [
                KeyboardButton(text="◀️ Orqaga")
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Lokatsiyani yuboring..."
    )
    return keyboard
