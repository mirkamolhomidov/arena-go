from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu():
    """Asosiy menyu klaviaturasi"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📍 Stadion topish"),
            ],
            [
                KeyboardButton(text="📅 Mening bronlarim"),
            ],
            [
                KeyboardButton(text="⚙️ Sozlamalar"),
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Tanlang..."
    )
    return keyboard


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
