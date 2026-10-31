from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
import re

import httpx
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.bot.handlers.user.stadium_common import (
    build_local_stadiums_message,
    format_amenities,
    format_condition_score,
    format_field_size,
    get_booking_status_badge,
    format_price,
    format_time_value,
    normalize_booking_status,
    stadium_cache,
)
from app.bot.keyboards.main_menu import get_main_menu_for_user
from app.bot.states.user import BookingFlow
from app.core.config import settings


router = Router()
TIME_RANGE_RE = re.compile(r"^\s*(\d{1,2}[:.]\d{2})\s*[-–]\s*(\d{1,2}[:.]\d{2})\s*$")


async def fetch_user_data(telegram_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.BASE_URL}/users/{telegram_id}",
            timeout=15.0,
        )

    if response.status_code != 200:
        return None

    return response.json()


async def fetch_local_stadiums(local_area_id: int) -> list[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.BASE_URL}/stadiums/location",
            params={"local_area_id": local_area_id},
            timeout=15.0,
        )

    response.raise_for_status()

    return response.json()


async def send_local_stadiums_overview(message: Message, telegram_id: int | None = None):
    telegram_id = telegram_id or message.from_user.id

    try:
        user_data = await fetch_user_data(telegram_id)
        if not user_data:
            await message.answer(
                "❌ Foydalanuvchi ma'lumotlari topilmadi. Avval /start orqali ro'yxatdan o'ting.",
                reply_markup=await get_main_menu_for_user(telegram_id),
            )
            return

        stadiums = await fetch_local_stadiums(user_data["local_area_id"])
        text, keyboard = build_local_stadiums_message(stadiums)

        await message.answer(
            text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    except httpx.HTTPError:
        await message.answer(
            "❌ Stadionlar ro'yxatini olib bo'lmadi. Birozdan keyin qayta urinib ko'ring.",
            reply_markup=await get_main_menu_for_user(telegram_id),
        )


def build_date_keyboard(stadium_id: int) -> InlineKeyboardMarkup:
    rows = []
    buttons = []
    today = date.today()

    for offset in range(7):
        current_date = today + timedelta(days=offset)

        if offset == 0:
            label = f"Bugun {current_date.strftime('%d.%m')}"
        elif offset == 1:
            label = f"Ertaga {current_date.strftime('%d.%m')}"
        else:
            label = current_date.strftime("%d.%m")

        buttons.append(
            InlineKeyboardButton(
                text=label,
                callback_data=f"bookdate_{stadium_id}_{current_date.isoformat()}",
            )
        )

    for index in range(0, len(buttons), 2):
        rows.append(buttons[index:index + 2])

    rows.append([
        InlineKeyboardButton(
            text="❌ Bekor qilish",
            callback_data="cancel_create_booking",
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_booking_prompt_keyboard(stadium_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📅 Boshqa sana tanlash",
                    callback_data=f"book_stadium_{stadium_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data="cancel_create_booking",
                )
            ],
        ]
    )


def build_my_bookings_keyboard(bookings: list[dict]) -> InlineKeyboardMarkup | None:
    if not bookings:
        return None

    keyboard_rows = []
    for booking in bookings:
        title = booking["stadium_name"]
        short_title = title if len(title) <= 18 else f"{title[:15]}..."
        time_part = f"{str(booking['start_time'])[:5]}"

        keyboard_rows.append([
            InlineKeyboardButton(
                text=f"❌ {short_title} | {time_part}",
                callback_data=f"cancel_booking_{booking['id']}",
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard_rows)


def build_cancel_confirmation_keyboard(booking_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Ha, bekor qilish",
                    callback_data=f"confirm_cancel_booking_{booking_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="↩️ Orqaga",
                    callback_data="show_my_bookings",
                )
            ],
        ]
    )


def format_booked_slots(bookings: list[dict]) -> str:
    if not bookings:
        return "Hozircha bu sana uchun band vaqtlar yo'q."

    lines = []
    for booking in bookings:
        status = normalize_booking_status(booking.get("status"))
        status_note = " (tasdiqlanmoqda)" if status == "pending" else ""
        lines.append(
            f"• {format_time_value(booking['start_time'])} - "
            f"{format_time_value(booking['end_time'])}{status_note}"
        )

    return "\n".join(lines)


def parse_time_range(text: str):
    match = TIME_RANGE_RE.match(text)
    if not match:
        return None

    start_raw = match.group(1).replace(".", ":")
    end_raw = match.group(2).replace(".", ":")

    try:
        start_time = datetime.strptime(start_raw, "%H:%M").time()
        end_time = datetime.strptime(end_raw, "%H:%M").time()
    except ValueError:
        return None

    return start_time, end_time


def calculate_total_price(price_per_hour, start_time: str, end_time: str) -> str | None:
    try:
        price = Decimal(str(price_per_hour))
        start_dt = datetime.strptime(start_time, "%H:%M")
        end_dt = datetime.strptime(end_time, "%H:%M")
        hours = Decimal((end_dt - start_dt).seconds) / Decimal(3600)
        total = price * hours
        return f"{float(total):,.0f}"
    except (InvalidOperation, ValueError, TypeError):
        return None


async def fetch_stadium_day_bookings(stadium_id: int, booking_date: str) -> list[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.BASE_URL}/bookings/",
            params={
                "stadium_id": stadium_id,
                "booking_date": booking_date,
            },
            timeout=15.0,
        )

    response.raise_for_status()

    payload = response.json()
    return payload.get("data", [])


async def fetch_my_bookings(telegram_id: int) -> list[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.BASE_URL}/bookings/my/{telegram_id}",
            timeout=15.0,
        )

    response.raise_for_status()

    payload = response.json()
    return payload.get("data", [])


def build_my_bookings_text(bookings: list[dict]) -> str:
    if not bookings:
        return (
            "📅 <b>Mening bronlarim va so'rovlarim</b>\n\n"
            "Sizda hozircha aktiv bron yoki so'rov yo'q."
        )

    text = "📅 <b>Mening bronlarim va so'rovlarim</b>\n\n"
    for index, booking in enumerate(bookings, 1):
        price = format_price(booking.get("price_per_hour"))
        text += f"<b>{index}. {booking['stadium_name']}</b>\n"
        text += f"   📅 {booking['booking_date']}\n"
        text += (
            f"   ⏰ {format_time_value(booking['start_time'])} - "
            f"{format_time_value(booking['end_time'])}\n"
        )
        text += f"   {get_booking_status_badge(booking.get('status'))}\n"
        text += f"   💰 {price} so'm/soat\n"
        text += f"   🏠 {booking['stadium_address']}\n\n"

    return text


async def show_user_bookings(message: Message):
    try:
        bookings = await fetch_my_bookings(message.from_user.id)
        keyboard = build_my_bookings_keyboard(bookings)
        await message.answer(
            build_my_bookings_text(bookings),
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    except httpx.HTTPError:
        await message.answer(
            "❌ Bronlar ro'yxatini olib bo'lmadi. Birozdan keyin urinib ko'ring."
        )


@router.message(F.text == "🏘 Hududimdagi stadionlar")
async def show_local_stadiums(message: Message):
    await send_local_stadiums_overview(message)


@router.callback_query(F.data == "back_to_local_stadiums")
async def back_to_local_stadiums(callback: CallbackQuery):
    try:
        user_data = await fetch_user_data(callback.from_user.id)
        if not user_data:
            await callback.answer(
                "❌ Foydalanuvchi ma'lumotlari topilmadi.",
                show_alert=True,
            )
            return

        stadiums = await fetch_local_stadiums(user_data["local_area_id"])
        text, keyboard = build_local_stadiums_message(stadiums)
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    except httpx.HTTPError:
        await callback.answer(
            "❌ Stadionlar ro'yxatini olib bo'lmadi.",
            show_alert=True,
        )
        return

    await callback.answer()


@router.callback_query(F.data.startswith("book_stadium_"))
async def start_booking(callback: CallbackQuery, state: FSMContext):
    stadium_id = callback.data.split("_")[-1]
    stadium = stadium_cache.get(stadium_id)

    if not stadium:
        await callback.answer(
            "❌ Stadion ma'lumotlari topilmadi. Stadionni qayta ochib urinib ko'ring.",
            show_alert=True,
        )
        return

    await state.clear()
    await state.set_state(BookingFlow.choosing_date)
    await state.update_data(
        stadium_id=int(stadium_id),
        stadium_name=stadium.get("name", "Noma'lum stadion"),
        stadium_address=stadium.get("address", "Manzil ko'rsatilmagan"),
        price_per_hour=stadium.get("price_per_hour", 0),
        stadium_field_size=format_field_size(stadium.get("field_size")),
        stadium_condition_score=format_condition_score(stadium.get("condition_score")),
        stadium_amenities=format_amenities(stadium.get("amenities")),
    )

    stadium_name = stadium.get("name", "Noma'lum stadion")
    stadium_address = stadium.get("address", "Manzil ko'rsatilmagan")

    booking_text = (
        f"📅 <b>{stadium_name} uchun bron</b>\n\n"
        f"🏠 {stadium_address}\n"
        f"👥 Maydon: {format_field_size(stadium.get('field_size'))}\n"
        f"⭐️ Holati: {format_condition_score(stadium.get('condition_score'))}\n"
        f"💰 Narx: {format_price(stadium.get('price_per_hour'))} so'm/soat\n\n"
        f"💡 Qulayliklar: {format_amenities(stadium.get('amenities'))}\n\n"
        "📆 Bron qilish uchun sanani tanlang:"
    )

    await callback.message.answer(
        booking_text,
        reply_markup=build_date_keyboard(int(stadium_id)),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("bookdate_"))
async def choose_booking_date(callback: CallbackQuery, state: FSMContext):
    _, stadium_id, selected_date = callback.data.split("_", 2)
    state_data = await state.get_data()

    if state_data.get("stadium_id") != int(stadium_id):
        await state.update_data(stadium_id=int(stadium_id))

    try:
        bookings = await fetch_stadium_day_bookings(int(stadium_id), selected_date)
    except httpx.HTTPError:
        await callback.answer(
            "❌ Band vaqtlarni olib bo'lmadi. Qayta urinib ko'ring.",
            show_alert=True,
        )
        return

    await state.set_state(BookingFlow.waiting_time_range)
    await state.update_data(booking_date=selected_date)

    prompt_text = (
        f"📆 <b>Sana tanlandi:</b> {selected_date}\n\n"
        f"🏟 {state_data.get('stadium_name', 'Stadion')}\n"
        f"👥 Maydon: {state_data.get('stadium_field_size', '-')}\n"
        f"⭐️ Holati: {state_data.get('stadium_condition_score', '-')}\n\n"
        f"🔒 <b>Band vaqtlar:</b>\n{format_booked_slots(bookings)}\n\n"
        "✍️ Vaqt oralig'ini yuboring.\n"
        "Masalan: <code>09:00-10:30</code>"
    )

    await callback.message.edit_text(
        prompt_text,
        reply_markup=build_booking_prompt_keyboard(int(stadium_id)),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(BookingFlow.choosing_date)
async def wrong_booking_date_input(message: Message):
    await message.answer(
        "📆 Iltimos, sanani tugmalar orqali tanlang."
    )


@router.message(BookingFlow.waiting_time_range)
async def complete_booking(message: Message, state: FSMContext):
    parsed_range = parse_time_range(message.text or "")
    if not parsed_range:
        await message.answer(
            "❌ Vaqt formatini to'g'ri yuboring.\n"
            "Namuna: <code>09:00-10:30</code>",
            parse_mode="HTML",
        )
        return

    start_time, end_time = parsed_range
    if start_time >= end_time:
        await message.answer(
            "❌ Boshlanish vaqti tugash vaqtidan oldin bo'lishi kerak."
        )
        return

    state_data = await state.get_data()
    payload = {
        "stadium_id": state_data["stadium_id"],
        "user_telegram_id": message.from_user.id,
        "booking_date": state_data["booking_date"],
        "start_time": start_time.strftime("%H:%M"),
        "end_time": end_time.strftime("%H:%M"),
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.BASE_URL}/bookings/create-booking",
                json=payload,
                timeout=15.0,
            )
    except httpx.HTTPError:
        await message.answer(
            "❌ Bron yaratishda server bilan bog'lanib bo'lmadi. Qayta urinib ko'ring."
        )
        return

    if response.status_code != 200:
        detail = response.text
        try:
            detail = response.json().get("detail", detail)
        except Exception:
            pass

        await message.answer(
            f"❌ {detail}\n\n"
            "Qayta urinib ko'ring yoki boshqa vaqt yuboring.",
        )
        return

    total_price = calculate_total_price(
        state_data.get("price_per_hour"),
        payload["start_time"],
        payload["end_time"],
    )

    success_stadium_name = state_data.get("stadium_name", "Stadion")
    success_stadium_address = state_data.get(
        "stadium_address",
        "Manzil ko'rsatilmagan",
    )

    success_text = (
        f"✅ <b>Bron so'rovi yuborildi</b>\n\n"
        f"🏟 {success_stadium_name}\n"
        f"🏠 {success_stadium_address}\n"
        f"📅 {state_data['booking_date']}\n"
        f"⏰ {payload['start_time']} - {payload['end_time']}\n"
        f"💰 Narx: {format_price(state_data.get('price_per_hour'))} so'm/soat\n"
    )

    if total_price is not None:
        success_text += f"🧾 Taxminiy jami: {total_price} so'm\n"

    success_text += "\n⏳ Admin tasdiqlagandan keyin bron faollashadi."

    await state.clear()
    await message.answer(
        success_text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📅 Mening bronlarim",
                        callback_data="show_my_bookings",
                    )
                ]
            ]
        ),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "cancel_create_booking")
async def cancel_booking_flow(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Bron qilish jarayoni bekor qilindi.")
    await callback.answer()


@router.message(F.text == "📅 Mening bronlarim")
async def my_bookings(message: Message):
    await show_user_bookings(message)


@router.callback_query(F.data == "show_my_bookings")
async def my_bookings_callback(callback: CallbackQuery):
    try:
        bookings = await fetch_my_bookings(callback.from_user.id)
    except httpx.HTTPError:
        await callback.answer(
            "❌ Bronlar ro'yxatini olib bo'lmadi.",
            show_alert=True,
        )
        return

    keyboard = build_my_bookings_keyboard(bookings)

    await callback.message.answer(
        build_my_bookings_text(bookings),
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cancel_booking_"))
async def ask_cancel_booking(callback: CallbackQuery):
    booking_id = callback.data.split("_")[-1]
    await callback.message.answer(
        "❓ Ushbu bronni bekor qilmoqchimisiz?",
        reply_markup=build_cancel_confirmation_keyboard(int(booking_id)),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_cancel_booking_"))
async def confirm_cancel_booking(callback: CallbackQuery):
    booking_id = callback.data.split("_")[-1]

    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{settings.BASE_URL}/bookings/cancel-booking/{booking_id}",
                params={"user_telegram_id": callback.from_user.id},
                timeout=15.0,
            )
    except httpx.HTTPError:
        await callback.message.edit_text(
            "❌ Bronni bekor qilishda server bilan bog'lanib bo'lmadi."
        )
        await callback.answer()
        return

    if response.status_code != 200:
        detail = response.text
        try:
            detail = response.json().get("detail", detail)
        except Exception:
            pass

        await callback.message.edit_text(f"❌ {detail}")
        await callback.answer()
        return

    await callback.message.edit_text("✅ Bron yoki so'rov bekor qilindi.")

    try:
        bookings = await fetch_my_bookings(callback.from_user.id)
    except httpx.HTTPError:
        await callback.answer(
            "✅ Bron bekor qilindi, lekin yangilangan ro'yxatni olib bo'lmadi.",
            show_alert=True,
        )
        return

    keyboard = build_my_bookings_keyboard(bookings)
    await callback.message.answer(
        build_my_bookings_text(bookings),
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()
