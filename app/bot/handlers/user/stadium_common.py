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
        start_time = format_time_value(stadium.get("start_time"))
        end_time = format_time_value(stadium.get("end_time"))
        price = format_price(stadium.get("price_per_hour"))

        text += f"<b>{idx}. {name}</b>\n"
        text += f"   ⏰ {start_time} - {end_time}\n"
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
