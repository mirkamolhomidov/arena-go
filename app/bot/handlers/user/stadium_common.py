from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


stadium_cache: dict[str, dict] = {}
search_results_cache: dict[int, list[dict]] = {}


def cache_stadiums(stadiums: list[dict]) -> None:
    for stadium in stadiums:
        stadium_id = stadium.get("id") or stadium.get("stadium_id")
        if stadium_id is not None:
            stadium_cache[str(stadium_id)] = stadium


def format_price(value) -> str:
    try:
        return f"{float(value):,.0f}"
    except (TypeError, ValueError):
        return "0"


def format_time_value(value) -> str:
    if value is None:
        return "-"

    value_str = str(value)
    return value_str[:5] if len(value_str) >= 5 else value_str


def format_field_size(value) -> str:
    if value is None:
        return "-"

    value_str = str(value).strip()
    if not value_str:
        return "-"

    return value_str.replace("x", "×").replace("X", "×")


def format_condition_score(value) -> str:
    if value is None or value == "":
        return "-"

    return f"{value}/10"


def format_amenities(value) -> str:
    if value is None:
        return "Ko'rsatilmagan"

    value_str = str(value).strip()
    return value_str or "Ko'rsatilmagan"


def normalize_booking_status(value) -> str:
    if value is None:
        return ""

    raw_value = getattr(value, "value", value)
    value_str = str(raw_value).strip().lower()
    if "." in value_str:
        value_str = value_str.split(".")[-1]
    return value_str


def get_booking_status_badge(value) -> str:
    status = normalize_booking_status(value)
    mapping = {
        "pending": "⏳ Tasdiq kutilmoqda",
        "confirmed": "✅ Tasdiqlangan",
        "cancelled": "❌ Bekor qilingan",
    }
    return mapping.get(status, "ℹ️ Holati noma'lum")


def build_local_stadiums_message(stadiums: list[dict]):
    if not stadiums:
        return (
            "🏟 <b>Hududingizdagi stadionlar</b>\n\n"
            "Afsuski, siz tanlagan hududda hali stadion topilmadi.\n"
            "📍 Yaqin stadionlarni topish uchun lokatsiya qidiruvidan foydalaning.",
            None,
        )

    cache_stadiums(stadiums)

    text = "🏟 <b>Hududingizdagi stadionlar</b>\n\n"
    keyboard_buttons = []

    for idx, stadium in enumerate(stadiums, 1):
        stadium["_list_source"] = "home"
        stadium_id = stadium.get("id") or stadium.get("stadium_id") or idx
        name = stadium.get("name", "Noma'lum stadion")
        short_name = name if len(name) <= 18 else f"{name[:15]}..."
        address = stadium.get("address", "Manzil ko'rsatilmagan")
        price = format_price(stadium.get("price_per_hour"))
        field_size = format_field_size(stadium.get("field_size"))
        condition_score = format_condition_score(stadium.get("condition_score"))

        text += f"<b>{idx}. {name}</b>\n"
        text += f"   👥 Maydon: {field_size}\n"
        text += f"   ⭐️ Holati: {condition_score}\n"
        text += f"   💰 {price} so'm/soat\n"
        text += f"   🏠 {address}\n\n"

        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"ℹ️ {short_name}",
                callback_data=f"stadium_detail_{stadium_id}",
            ),
            InlineKeyboardButton(
                text="📅 Bron qilish",
                callback_data=f"book_stadium_{stadium_id}",
            ),
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    return text, keyboard
