from datetime import date
from decimal import Decimal, InvalidOperation

import httpx
from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

from app.bot.handlers.user.stadium_common import (
    format_amenities,
    format_condition_score,
    format_field_size,
    format_price,
    format_time_value,
    get_booking_status_badge,
    normalize_booking_status,
)
from app.bot.keyboards.main_menu import get_main_menu_for_user
from app.bot.states.user import AdminPanelFlow
from app.core.config import settings


router = Router()
managed_stadium_cache: dict[str, dict] = {}
SUPERADMIN_ONLY_TEXT = "Bu bo'lim faqat superadmin uchun."
STADIUM_LOCATION_STATES = (
    AdminPanelFlow.choosing_stadium_region,
    AdminPanelFlow.choosing_stadium_district,
    AdminPanelFlow.choosing_stadium_local_area,
)
STADIUM_CREATION_STATES = (
    AdminPanelFlow.waiting_stadium_name,
    AdminPanelFlow.waiting_stadium_address,
    AdminPanelFlow.waiting_stadium_phone,
    AdminPanelFlow.waiting_stadium_price,
    AdminPanelFlow.choosing_stadium_field_size,
    AdminPanelFlow.waiting_stadium_condition_score,
    AdminPanelFlow.waiting_stadium_amenities,
    AdminPanelFlow.waiting_stadium_location,
    *STADIUM_LOCATION_STATES,
)


async def fetch_user_profile(telegram_id: int) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.BASE_URL}/users/{telegram_id}",
            timeout=15.0,
        )

    response.raise_for_status()
    return response.json()


async def fetch_managed_stadiums(telegram_id: int) -> list[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.BASE_URL}/stadiums/managed",
            params={"telegram_id": telegram_id},
            timeout=15.0,
        )

    response.raise_for_status()
    return response.json()


async def fetch_admin_bookings(
    telegram_id: int,
    stadium_id: int | None = None,
    booking_date: str | None = None,
) -> list[dict]:
    params = {}
    if stadium_id is not None:
        params["stadium_id"] = stadium_id
    if booking_date is not None:
        params["booking_date"] = booking_date

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.BASE_URL}/bookings/admin/{telegram_id}",
            params=params,
            timeout=15.0,
        )

    response.raise_for_status()
    payload = response.json()
    return payload.get("data", [])


async def cancel_admin_booking(admin_telegram_id: int, booking_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{settings.BASE_URL}/bookings/cancel-booking/{booking_id}",
            params={"admin_telegram_id": admin_telegram_id},
            timeout=15.0,
        )

    response.raise_for_status()
    return response.json()


async def approve_admin_booking(admin_telegram_id: int, booking_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{settings.BASE_URL}/bookings/approve-booking/{booking_id}",
            params={"admin_telegram_id": admin_telegram_id},
            timeout=15.0,
        )

    response.raise_for_status()
    return response.json()


async def assign_stadium_admin(
    actor_telegram_id: int,
    stadium_id: int,
    phone: str,
):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.BASE_URL}/users/create/admin",
            params={"actor_telegram_id": actor_telegram_id},
            json={
                "phone": phone,
                "stadium_id": stadium_id,
            },
            timeout=15.0,
        )

    response.raise_for_status()
    return response.json()


async def create_superadmin(actor_telegram_id: int, phone: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.BASE_URL}/users/create/superadmin",
            params={"actor_telegram_id": actor_telegram_id},
            json={"phone": phone},
            timeout=15.0,
        )

    response.raise_for_status()
    return response.json()


async def fetch_superadmins(actor_telegram_id: int) -> list[dict]:
    """Fetch the current superadmin list for management screens."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.BASE_URL}/users/superadmins",
            params={"actor_telegram_id": actor_telegram_id},
            timeout=15.0,
        )

    response.raise_for_status()
    payload = response.json()
    return payload.get("data", [])


async def remove_superadmin_user(actor_telegram_id: int, user_id: int):
    """Demote a superadmin through the users API."""
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{settings.BASE_URL}/users/superadmins/{user_id}",
            params={"actor_telegram_id": actor_telegram_id},
            timeout=15.0,
        )

    response.raise_for_status()
    return response.json()


async def create_stadium(actor_telegram_id: int, payload: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.BASE_URL}/stadiums/create",
            params={"actor_telegram_id": actor_telegram_id},
            json=payload,
            timeout=20.0,
        )

    response.raise_for_status()
    return response.json()


async def fetch_stadium_admins(actor_telegram_id: int, stadium_id: int) -> list[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.BASE_URL}/users/stadium-admins/{stadium_id}",
            params={"actor_telegram_id": actor_telegram_id},
            timeout=15.0,
        )

    response.raise_for_status()
    payload = response.json()
    return payload.get("data", [])


async def remove_stadium_admin(actor_telegram_id: int, stadium_admin_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{settings.BASE_URL}/users/stadium-admins/{stadium_admin_id}",
            params={"actor_telegram_id": actor_telegram_id},
            timeout=15.0,
        )

    response.raise_for_status()
    return response.json()


async def fetch_regions() -> list[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.BASE_URL}/locations/regions",
            timeout=15.0,
        )

    response.raise_for_status()
    return response.json()


async def fetch_districts(region_id: int) -> list[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.BASE_URL}/locations/districts",
            params={"region_id": region_id},
            timeout=15.0,
        )

    response.raise_for_status()
    return response.json()


async def fetch_local_areas(district_id: int) -> list[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.BASE_URL}/locations/local-areas",
            params={"district_id": district_id},
            timeout=15.0,
        )

    response.raise_for_status()
    return response.json()


def cache_stadiums(stadiums: list[dict]) -> None:
    for stadium in stadiums:
        managed_stadium_cache[str(stadium["id"])] = stadium


def build_inline_cancel_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data=callback_data,
                )
            ]
        ]
    )


def build_location_share_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Lokatsiyani yuborish", request_location=True)],
            [KeyboardButton(text="❌ Bekor qilish")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Lokatsiyani yuboring...",
    )


def build_location_choice_keyboard(items: list[dict], prefix: str) -> InlineKeyboardMarkup:
    rows = []
    for item in items:
        rows.append([
            InlineKeyboardButton(
                text=item["name"],
                callback_data=f"{prefix}{item['id']}",
            )
        ])

    rows.append([
        InlineKeyboardButton(
            text="❌ Bekor qilish",
            callback_data="superadmin_cancel_stadium_create",
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_field_size_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="5x5", callback_data="superadmin_pick_size_5x5"),
            InlineKeyboardButton(text="6x6", callback_data="superadmin_pick_size_6x6"),
            InlineKeyboardButton(text="7x7", callback_data="superadmin_pick_size_7x7"),
        ],
        [
            InlineKeyboardButton(
                text="❌ Bekor qilish",
                callback_data="superadmin_cancel_stadium_create",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_admin_panel_message(stadiums: list[dict], role: str):
    text = "🛠 <b>Admin panel</b>\n\n"
    keyboard_rows = []

    if role == "superadmin":
        keyboard_rows.append([
            InlineKeyboardButton(
                text="🏟 Stadion qo'shish",
                callback_data="superadmin_create_stadium_start",
            ),
            InlineKeyboardButton(
                text="👑 Superadmin qo'shish",
                callback_data="superadmin_promote_start",
            ),
        ])
        keyboard_rows.append([
            InlineKeyboardButton(
                text="🧾 Superadminlarni boshqarish",
                callback_data="superadmin_manage_superadmins",
            )
        ])

    if stadiums:
        cache_stadiums(stadiums)
        section_title = (
            "Tizimdagi stadionlar:"
            if role == "superadmin"
            else "Boshqarishingiz mumkin bo'lgan stadionlar:"
        )
        text += f"{section_title}\n\n"

        keyboard_rows.append([
            InlineKeyboardButton(
                text="📅 Bugungi bron va so'rovlar",
                callback_data="admin_today_bookings",
            )
        ])

        if role == "superadmin":
            keyboard_rows.append([
                InlineKeyboardButton(
                    text="➕ Admin tayinlash",
                    callback_data="superadmin_assign_start",
                ),
                InlineKeyboardButton(
                    text="👥 Adminlarni boshqarish",
                    callback_data="superadmin_manage_start",
                ),
            ])

        for index, stadium in enumerate(stadiums, 1):
            text += f"<b>{index}. {stadium['name']}</b>\n"
            text += f"   👥 Maydon: {format_field_size(stadium.get('field_size'))}\n"
            text += f"   ⭐️ Holati: {format_condition_score(stadium.get('condition_score'))}\n"
            text += f"   💰 {format_price(stadium.get('price_per_hour'))} so'm/soat\n"
            text += f"   🏠 {stadium.get('address', 'Manzil yo`q')}\n\n"

            keyboard_rows.append([
                InlineKeyboardButton(
                    text=f"📋 {stadium['name']}",
                    callback_data=f"admin_stadium_{stadium['id']}",
                )
            ])
    else:
        if role == "superadmin":
            text += (
                "Hozircha stadion topilmadi.\n"
                "Quyidagi tugmalar orqali stadion yoki superadmin qo'shishingiz mumkin."
            )
        else:
            text += "Sizga hali stadion biriktirilmagan."

    keyboard = (
        InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
        if keyboard_rows
        else None
    )
    return text, keyboard


def build_date_keyboard(stadium_id: int) -> InlineKeyboardMarkup:
    from datetime import timedelta

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
                callback_data=f"admin_day_{stadium_id}_{current_date.isoformat()}",
            )
        )

    for index in range(0, len(buttons), 2):
        rows.append(buttons[index:index + 2])

    rows.append([
        InlineKeyboardButton(
            text="◀️ Panelga qaytish",
            callback_data="admin_panel_home",
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_stadium_selection_keyboard(stadiums: list[dict], prefix: str) -> InlineKeyboardMarkup:
    rows = []
    for stadium in stadiums:
        rows.append([
            InlineKeyboardButton(
                text=stadium["name"],
                callback_data=f"{prefix}{stadium['id']}",
            )
        ])

    rows.append([
        InlineKeyboardButton(
            text="◀️ Panelga qaytish",
            callback_data="admin_panel_home",
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_admin_bookings_keyboard(stadium_id: int, context: str, bookings: list[dict]):
    keyboard_rows = []

    for booking in bookings:
        customer_name = booking.get("customer_first_name") or "Mijoz"
        short_name = customer_name if len(customer_name) <= 12 else f"{customer_name[:9]}..."
        time_range = (
            f"{format_time_value(booking['start_time'])} - "
            f"{format_time_value(booking['end_time'])}"
        )
        if normalize_booking_status(booking.get("status")) == "pending":
            keyboard_rows.append([
                InlineKeyboardButton(
                    text=f"✅ {time_range} | {short_name}",
                    callback_data=f"admin_approve_{booking['id']}_{stadium_id}_{context}",
                ),
                InlineKeyboardButton(
                    text="❌ Rad etish",
                    callback_data=f"admin_cancel_{booking['id']}_{stadium_id}_{context}",
                ),
            ])
        else:
            keyboard_rows.append([
                InlineKeyboardButton(
                    text=f"❌ {time_range} | {short_name}",
                    callback_data=f"admin_cancel_{booking['id']}_{stadium_id}_{context}",
                )
            ])

    if context != "today":
        keyboard_rows.append([
            InlineKeyboardButton(
                text="📅 Boshqa sana",
                callback_data=f"admin_stadium_{stadium_id}",
            )
        ])

    keyboard_rows.append([
        InlineKeyboardButton(
            text="◀️ Panelga qaytish",
            callback_data="admin_panel_home",
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard_rows)


def build_admin_bookings_text(stadium: dict, booking_date: str, bookings: list[dict]) -> str:
    text = (
        f"📋 <b>{stadium['name']}</b>\n\n"
        f"📅 Sana: {booking_date}\n"
        f"🏠 {stadium.get('address', 'Manzil yo`q')}\n"
        f"👥 Maydon: {format_field_size(stadium.get('field_size'))}\n"
        f"⭐️ Holati: {format_condition_score(stadium.get('condition_score'))}\n"
        f"💡 Qulayliklar: {format_amenities(stadium.get('amenities'))}\n\n"
    )

    if not bookings:
        return text + "Bu sana uchun bron yoki so'rov yo'q."

    text += "<b>Bron va so'rovlar:</b>\n\n"
    for index, booking in enumerate(bookings, 1):
        username = booking.get("customer_username")
        username_text = f"@{username}" if username else "-"
        text += (
            f"<b>{index}. {format_time_value(booking['start_time'])} - "
            f"{format_time_value(booking['end_time'])}</b>\n"
        )
        text += f"   {get_booking_status_badge(booking.get('status'))}\n"
        text += f"   👤 {booking.get('customer_first_name') or 'Noma`lum'}\n"
        text += f"   🪪 {username_text}\n"
        text += f"   📞 {booking.get('customer_phone') or '-'}\n\n"

    return text


def build_today_bookings_text(bookings: list[dict]) -> str:
    text = f"📅 <b>Bugungi bron va so'rovlar</b>\n\nSana: {date.today().isoformat()}\n\n"

    if not bookings:
        return text + "Bugun bron yoki so'rov yo'q."

    current_stadium = None
    for booking in bookings:
        if booking["stadium_name"] != current_stadium:
            current_stadium = booking["stadium_name"]
            text += f"<b>🏟 {current_stadium}</b>\n"
            text += f"   🏠 {booking.get('stadium_address') or '-'}\n\n"

        username = booking.get("customer_username")
        username_text = f"@{username}" if username else "-"
        text += (
            f"• {format_time_value(booking['start_time'])} - "
            f"{format_time_value(booking['end_time'])}\n"
        )
        text += f"  {get_booking_status_badge(booking.get('status'))}\n"
        text += f"  👤 {booking.get('customer_first_name') or 'Noma`lum'}\n"
        text += f"  🪪 {username_text}\n"
        text += f"  📞 {booking.get('customer_phone') or '-'}\n\n"

    return text


def build_today_bookings_keyboard(bookings: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for booking in bookings:
        stadium_name = booking.get("stadium_name", "Stadion")
        short_stadium = stadium_name if len(stadium_name) <= 14 else f"{stadium_name[:11]}..."
        time_range = (
            f"{format_time_value(booking['start_time'])} - "
            f"{format_time_value(booking['end_time'])}"
        )
        if normalize_booking_status(booking.get("status")) == "pending":
            rows.append([
                InlineKeyboardButton(
                    text=f"✅ {time_range} | {short_stadium}",
                    callback_data=(
                        f"admin_approve_{booking['id']}_{booking['stadium_id']}_today"
                    ),
                ),
                InlineKeyboardButton(
                    text="❌ Rad etish",
                    callback_data=(
                        f"admin_cancel_{booking['id']}_{booking['stadium_id']}_today"
                    ),
                ),
            ])
        else:
            rows.append([
                InlineKeyboardButton(
                    text=f"❌ {time_range} | {short_stadium}",
                    callback_data=(
                        f"admin_cancel_{booking['id']}_{booking['stadium_id']}_today"
                    ),
                )
            ])

    rows.append([
        InlineKeyboardButton(
            text="◀️ Panelga qaytish",
            callback_data="admin_panel_home",
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_stadium_admins_text(stadium: dict, admins: list[dict]) -> str:
    text = (
        f"👥 <b>{stadium['name']} adminlari</b>\n\n"
        f"🏠 {stadium.get('address', 'Manzil yo`q')}\n\n"
    )

    if not admins:
        return text + "Bu stadionga hali admin biriktirilmagan."

    for index, admin in enumerate(admins, 1):
        username = admin.get("username")
        username_text = f"@{username}" if username else "-"
        text += f"<b>{index}. {admin.get('first_name') or 'Noma`lum'}</b>\n"
        text += f"   🪪 {username_text}\n"
        text += f"   📞 {admin.get('phone') or '-'}\n\n"

    return text


def build_stadium_admins_keyboard(stadium_id: int, admins: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for admin in admins:
        name = admin.get("first_name") or "Admin"
        short_name = name if len(name) <= 14 else f"{name[:11]}..."
        rows.append([
            InlineKeyboardButton(
                text=f"❌ {short_name}",
                callback_data=(
                    f"superadmin_remove_{admin['stadium_admin_id']}_{stadium_id}"
                ),
            )
        ])

    rows.extend([
        [
            InlineKeyboardButton(
                text="➕ Admin qo'shish",
                callback_data=f"superadmin_assign_pick_{stadium_id}",
            )
        ],
        [
            InlineKeyboardButton(
                text="🏟 Boshqa stadion",
                callback_data="superadmin_manage_start",
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Panelga qaytish",
                callback_data="admin_panel_home",
            )
        ],
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_superadmins_text(superadmins: list[dict]) -> str:
    """Build the text block for the superadmin management screen."""
    text = "🧾 <b>Superadminlar</b>\n\n"

    if not superadmins:
        return text + "Hozircha superadmin topilmadi."

    for index, user in enumerate(superadmins, 1):
        username = user.get("username")
        username_text = f"@{username}" if username else "-"
        suffix = " (siz)" if not user.get("can_remove", False) else ""
        text += f"<b>{index}. {user.get('first_name') or 'Noma`lum'}</b>{suffix}\n"
        text += f"   🪪 {username_text}\n"
        text += f"   📞 {user.get('phone') or '-'}\n\n"

    return text


def build_superadmins_keyboard(superadmins: list[dict]) -> InlineKeyboardMarkup:
    """Build action buttons for superadmin demotion actions."""
    rows = []

    for user in superadmins:
        if not user.get("can_remove"):
            continue

        name = user.get("first_name") or "Superadmin"
        short_name = name if len(name) <= 14 else f"{name[:11]}..."
        rows.append([
            InlineKeyboardButton(
                text=f"❌ {short_name}",
                callback_data=f"superadmin_demote_{user['user_id']}",
            )
        ])

    rows.extend([
        [
            InlineKeyboardButton(
                text="👑 Superadmin qo'shish",
                callback_data="superadmin_promote_start",
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Panelga qaytish",
                callback_data="admin_panel_home",
            )
        ],
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def extract_error_detail(exc: httpx.HTTPStatusError, default: str) -> str:
    detail = default
    try:
        payload = exc.response.json()
        raw_detail = payload.get("detail", default)
        if isinstance(raw_detail, list):
            pieces = []
            for item in raw_detail:
                if isinstance(item, dict):
                    pieces.append(item.get("msg", str(item)))
                else:
                    pieces.append(str(item))
            detail = "; ".join(pieces) or default
        elif isinstance(raw_detail, dict):
            detail = raw_detail.get("msg", default)
        else:
            detail = str(raw_detail)
    except Exception:
        detail = default
    return detail


def parse_phone_input(message: Message) -> str:
    phone = message.text or ""
    if message.contact:
        phone = message.contact.phone_number
    return phone.strip()


def parse_price_input(value: str) -> Decimal | None:
    normalized = value.replace(" ", "").replace(",", ".")
    try:
        amount = Decimal(normalized)
    except InvalidOperation:
        return None

    if amount <= 0:
        return None
    return amount


async def require_superadmin(telegram_id: int) -> dict | None:
    profile = await fetch_user_profile(telegram_id)
    if profile.get("role") != "superadmin":
        return None
    return profile


async def render_admin_panel_message(target, telegram_id: int, *, edit: bool = False):
    profile = await fetch_user_profile(telegram_id)
    stadiums = await fetch_managed_stadiums(telegram_id)
    text, keyboard = build_admin_panel_message(stadiums, profile.get("role", "user"))

    if edit:
        await target.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await target.answer(text, reply_markup=keyboard, parse_mode="HTML")


async def send_booking_status_notification(
    callback: CallbackQuery,
    booking: dict,
    action: str,
):
    admin_name = callback.from_user.full_name or "Admin"

    if action == "approved":
        title = "✅ <b>Bron so'rovingiz tasdiqlandi</b>"
    elif action == "rejected":
        title = "❌ <b>Bron so'rovingiz rad etildi</b>"
    else:
        title = "❌ <b>Broningiz bekor qilindi</b>"

    text = (
        f"{title}\n\n"
        f"🏟 Stadion: {booking.get('stadium_name', 'Stadion')}\n"
        f"📅 Sana: {booking.get('booking_date')}\n"
        f"⏰ {format_time_value(booking.get('start_time'))} - "
        f"{format_time_value(booking.get('end_time'))}\n"
        f"👤 Admin: {admin_name}"
    )

    try:
        await callback.bot.send_message(
            booking["user_telegram_id"],
            text,
            parse_mode="HTML",
        )
    except Exception:
        pass


@router.message(F.text == "🛠 Admin panel")
async def admin_panel_entry(message: Message, state: FSMContext):
    await state.clear()
    try:
        await render_admin_panel_message(message, message.from_user.id)
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        if status_code == 403:
            await message.answer("❌ Sizda admin panelga kirish huquqi yo'q.")
            return
        await message.answer("❌ Admin panelni yuklab bo'lmadi. Keyinroq urinib ko'ring.")


@router.callback_query(F.data == "admin_panel_home")
async def admin_panel_home(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await render_admin_panel_message(
            callback.message,
            callback.from_user.id,
            edit=True,
        )
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        if status_code == 403:
            await callback.answer(
                "Sizda admin panelga kirish huquqi yo'q.",
                show_alert=True,
            )
            return
        await callback.answer(
            "Admin panelni ochib bo'lmadi.",
            show_alert=True,
        )
        return

    await callback.answer()


@router.callback_query(F.data == "admin_today_bookings")
async def admin_today_bookings(callback: CallbackQuery):
    today_str = date.today().isoformat()

    try:
        bookings = await fetch_admin_bookings(
            callback.from_user.id,
            booking_date=today_str,
        )
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        if status_code == 403:
            await callback.answer(
                "Sizda bu bo'limni ko'rish huquqi yo'q.",
                show_alert=True,
            )
            return
        await callback.answer(
            "Bugungi bronlarni yuklab bo'lmadi.",
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        build_today_bookings_text(bookings),
        reply_markup=build_today_bookings_keyboard(bookings),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_stadium_"))
async def admin_stadium_detail(callback: CallbackQuery):
    stadium_id = callback.data.split("_")[-1]
    stadium = managed_stadium_cache.get(stadium_id)

    if not stadium:
        try:
            stadiums = await fetch_managed_stadiums(callback.from_user.id)
            cache_stadiums(stadiums)
            stadium = managed_stadium_cache.get(stadium_id)
        except httpx.HTTPStatusError:
            stadium = None

    if not stadium:
        await callback.answer(
            "Stadion ma'lumotini topib bo'lmadi.",
            show_alert=True,
        )
        return

    text = (
        f"🏟 <b>{stadium['name']}</b>\n\n"
        f"🏠 {stadium.get('address', 'Manzil yo`q')}\n"
        f"📞 {stadium.get('phone', '-')}\n"
        f"👥 Maydon o'lchami: {format_field_size(stadium.get('field_size'))}\n"
        f"⭐️ Stadion holati: {format_condition_score(stadium.get('condition_score'))}\n"
        f"💰 {format_price(stadium.get('price_per_hour'))} so'm/soat\n\n"
        f"💡 Qulayliklar: {format_amenities(stadium.get('amenities'))}\n\n"
        "📅 Bronlarni ko'rish uchun sanani tanlang:"
    )

    await callback.message.edit_text(
        text,
        reply_markup=build_date_keyboard(int(stadium_id)),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_day_"))
async def admin_day_bookings(callback: CallbackQuery):
    _, _, stadium_id, booking_date = callback.data.split("_", 3)
    stadium = managed_stadium_cache.get(stadium_id)

    if not stadium:
        await callback.answer(
            "Stadion ma'lumotini topib bo'lmadi.",
            show_alert=True,
        )
        return

    try:
        bookings = await fetch_admin_bookings(
            callback.from_user.id,
            stadium_id=int(stadium_id),
            booking_date=booking_date,
        )
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        if status_code == 403:
            await callback.answer(
                "Siz bu stadion bronlarini ko'ra olmaysiz.",
                show_alert=True,
            )
            return
        await callback.answer(
            "Bronlarni yuklab bo'lmadi.",
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        build_admin_bookings_text(stadium, booking_date, bookings),
        reply_markup=build_admin_bookings_keyboard(
            int(stadium_id),
            booking_date,
            bookings,
        ),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "superadmin_promote_start")
async def superadmin_promote_start(callback: CallbackQuery, state: FSMContext):
    try:
        profile = await require_superadmin(callback.from_user.id)
    except httpx.HTTPStatusError:
        profile = None

    if not profile:
        await callback.answer(SUPERADMIN_ONLY_TEXT, show_alert=True)
        return

    await state.clear()
    await state.set_state(AdminPanelFlow.waiting_superadmin_phone)
    await callback.message.answer(
        "👑 <b>Yangi superadmin qo'shish</b>\n\n"
        "Foydalanuvchining telefon raqamini yuboring.\n"
        "Namuna: <code>998901234567</code>",
        reply_markup=build_inline_cancel_keyboard("superadmin_cancel_promote"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "superadmin_manage_superadmins")
async def superadmin_manage_superadmins(callback: CallbackQuery):
    """Open the superadmin management screen for superadmin actors."""
    try:
        profile = await require_superadmin(callback.from_user.id)
        if not profile:
            await callback.answer(SUPERADMIN_ONLY_TEXT, show_alert=True)
            return

        superadmins = await fetch_superadmins(callback.from_user.id)
    except httpx.HTTPStatusError as exc:
        await callback.answer(
            extract_error_detail(exc, "Superadminlar ro'yxatini yuklab bo'lmadi."),
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        build_superadmins_text(superadmins),
        reply_markup=build_superadmins_keyboard(superadmins),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "superadmin_cancel_promote")
async def superadmin_cancel_promote(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await render_admin_panel_message(callback.message, callback.from_user.id, edit=True)
    await callback.answer("Superadmin qo'shish bekor qilindi.")


@router.callback_query(F.data.startswith("superadmin_demote_"))
async def superadmin_demote_handler(callback: CallbackQuery):
    """Demote a superadmin and refresh the management screen."""
    user_id = int(callback.data.split("_")[-1])

    try:
        await remove_superadmin_user(callback.from_user.id, user_id)
        superadmins = await fetch_superadmins(callback.from_user.id)
    except httpx.HTTPStatusError as exc:
        await callback.answer(
            extract_error_detail(exc, "Superadminni olib tashlab bo'lmadi."),
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        build_superadmins_text(superadmins),
        reply_markup=build_superadmins_keyboard(superadmins),
        parse_mode="HTML",
    )
    await callback.answer("Superadmin olib tashlandi.")


@router.message(AdminPanelFlow.waiting_superadmin_phone)
async def superadmin_promote_phone(message: Message, state: FSMContext):
    phone = parse_phone_input(message)
    if not phone:
        await message.answer("❌ Telefon raqam yuboring.")
        return

    try:
        result = await create_superadmin(message.from_user.id, phone)
    except httpx.HTTPStatusError as exc:
        await message.answer(f"❌ {extract_error_detail(exc, 'Superadmin qo`shib bo`lmadi.')}")
        return

    data = result.get("data", {})
    await state.clear()
    await message.answer(
        f"✅ <b>{data.get('first_name', 'Foydalanuvchi')}</b> superadmin qilindi.",
        reply_markup=await get_main_menu_for_user(message.from_user.id),
        parse_mode="HTML",
    )
    await render_admin_panel_message(message, message.from_user.id)


@router.callback_query(F.data == "superadmin_create_stadium_start")
async def superadmin_create_stadium_start(callback: CallbackQuery, state: FSMContext):
    try:
        profile = await require_superadmin(callback.from_user.id)
    except httpx.HTTPStatusError:
        profile = None

    if not profile:
        await callback.answer(SUPERADMIN_ONLY_TEXT, show_alert=True)
        return

    await state.clear()
    await state.set_state(AdminPanelFlow.waiting_stadium_name)
    await callback.message.answer(
        "🏟 <b>Yangi stadion qo'shish</b>\n\n"
        "1-qadam: stadion nomini yuboring.",
        reply_markup=build_inline_cancel_keyboard("superadmin_cancel_stadium_create"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "superadmin_cancel_stadium_create")
async def superadmin_cancel_stadium_create(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await render_admin_panel_message(callback.message, callback.from_user.id, edit=True)
    await callback.answer("Stadion qo'shish bekor qilindi.")


@router.message(StateFilter(*STADIUM_CREATION_STATES, AdminPanelFlow.waiting_superadmin_phone), F.text == "❌ Bekor qilish")
async def admin_panel_text_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Amal bekor qilindi.",
        reply_markup=await get_main_menu_for_user(message.from_user.id),
    )
    await render_admin_panel_message(message, message.from_user.id)


@router.message(AdminPanelFlow.waiting_stadium_name)
async def superadmin_stadium_name(message: Message, state: FSMContext):
    name = (message.text or "").strip()
    if len(name) < 3:
        await message.answer("❌ Stadion nomi kamida 3 ta harfdan iborat bo'lsin.")
        return

    await state.update_data(stadium_name=name)
    await state.set_state(AdminPanelFlow.waiting_stadium_address)
    await message.answer(
        "2-qadam: stadion manzilini yuboring.",
        reply_markup=build_inline_cancel_keyboard("superadmin_cancel_stadium_create"),
    )


@router.message(AdminPanelFlow.waiting_stadium_address)
async def superadmin_stadium_address(message: Message, state: FSMContext):
    address = (message.text or "").strip()
    if len(address) < 5:
        await message.answer("❌ Manzilni to'liqroq yuboring.")
        return

    await state.update_data(stadium_address=address)
    await state.set_state(AdminPanelFlow.waiting_stadium_phone)
    await message.answer(
        "3-qadam: stadion telefon raqamini yuboring.\n"
        "Namuna: <code>998901234567</code>",
        reply_markup=build_inline_cancel_keyboard("superadmin_cancel_stadium_create"),
        parse_mode="HTML",
    )


@router.message(AdminPanelFlow.waiting_stadium_phone)
async def superadmin_stadium_phone(message: Message, state: FSMContext):
    phone = parse_phone_input(message)
    if not phone:
        await message.answer("❌ Telefon raqam yuboring.")
        return

    await state.update_data(stadium_phone=phone)
    await state.set_state(AdminPanelFlow.waiting_stadium_price)
    await message.answer(
        "4-qadam: bir soatlik narxni yuboring.\n"
        "Masalan: <code>20000</code>",
        reply_markup=build_inline_cancel_keyboard("superadmin_cancel_stadium_create"),
        parse_mode="HTML",
    )


@router.message(AdminPanelFlow.waiting_stadium_price)
async def superadmin_stadium_price(message: Message, state: FSMContext):
    value = (message.text or "").strip()
    price = parse_price_input(value)
    if price is None:
        await message.answer("❌ Narxni son ko'rinishida yuboring. Masalan: 20000")
        return

    await state.update_data(stadium_price=str(price))
    await state.set_state(AdminPanelFlow.choosing_stadium_field_size)
    await message.answer(
        "5-qadam: maydon o'lchamini tanlang.",
        reply_markup=build_field_size_keyboard(),
    )


@router.callback_query(F.data.startswith("superadmin_pick_size_"))
async def superadmin_pick_field_size(callback: CallbackQuery, state: FSMContext):
    field_size = callback.data.split("_")[-1]
    await state.update_data(stadium_field_size=field_size)
    await state.set_state(AdminPanelFlow.waiting_stadium_condition_score)
    await callback.message.edit_text(
        "6-qadam: stadion holatini 0 dan 10 gacha baholang.\n"
        "Masalan: <code>8</code>",
        reply_markup=build_inline_cancel_keyboard("superadmin_cancel_stadium_create"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminPanelFlow.waiting_stadium_condition_score)
async def superadmin_stadium_condition_score(message: Message, state: FSMContext):
    raw_value = (message.text or "").strip()
    if not raw_value.isdigit():
        await message.answer("❌ Holatni 0 dan 10 gacha butun son qilib yuboring.")
        return

    condition_score = int(raw_value)
    if condition_score < 0 or condition_score > 10:
        await message.answer("❌ Holat 0 dan 10 gacha bo'lishi kerak.")
        return

    await state.update_data(stadium_condition_score=condition_score)
    await state.set_state(AdminPanelFlow.waiting_stadium_amenities)
    await message.answer(
        "7-qadam: qulayliklar va sharoitlar haqida yozing.\n"
        "Masalan: dush, razdivalka, suv, choy, butsi ijarasi.\n"
        "Agar yo'q bo'lsa, <code>yo'q</code> deb yozing.",
        reply_markup=build_inline_cancel_keyboard("superadmin_cancel_stadium_create"),
        parse_mode="HTML",
    )


@router.message(AdminPanelFlow.waiting_stadium_amenities)
async def superadmin_stadium_amenities(message: Message, state: FSMContext):
    amenities = (message.text or "").strip()
    if not amenities:
        await message.answer("❌ Qulayliklar haqida kamida qisqa info yuboring.")
        return

    try:
        regions = await fetch_regions()
    except httpx.HTTPError:
        await message.answer("❌ Hududlar ro'yxatini olib bo'lmadi. Qaytadan urinib ko'ring.")
        return

    await state.update_data(stadium_amenities=amenities)
    await state.set_state(AdminPanelFlow.choosing_stadium_region)
    await message.answer(
        "8-qadam: stadion joylashgan viloyatni tanlang.",
        reply_markup=build_location_choice_keyboard(
            regions,
            "superadmin_pick_region_",
        ),
    )


@router.callback_query(F.data.startswith("superadmin_pick_region_"))
async def superadmin_pick_region(callback: CallbackQuery, state: FSMContext):
    region_id = int(callback.data.split("_")[-1])

    try:
        districts = await fetch_districts(region_id)
    except httpx.HTTPError:
        await callback.answer("Tumanlarni yuklab bo'lmadi.", show_alert=True)
        return

    if not districts:
        await callback.answer("Bu viloyat uchun tuman topilmadi.", show_alert=True)
        return

    await state.update_data(stadium_region_id=region_id)
    await state.set_state(AdminPanelFlow.choosing_stadium_district)
    await callback.message.edit_text(
        "9-qadam: stadion joylashgan tumanni tanlang.",
        reply_markup=build_location_choice_keyboard(
            districts,
            "superadmin_pick_district_",
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("superadmin_pick_district_"))
async def superadmin_pick_district(callback: CallbackQuery, state: FSMContext):
    district_id = int(callback.data.split("_")[-1])

    try:
        local_areas = await fetch_local_areas(district_id)
    except httpx.HTTPError:
        await callback.answer("Hududlarni yuklab bo'lmadi.", show_alert=True)
        return

    if not local_areas:
        await callback.answer("Bu tuman uchun hudud topilmadi.", show_alert=True)
        return

    await state.update_data(stadium_district_id=district_id)
    await state.set_state(AdminPanelFlow.choosing_stadium_local_area)
    await callback.message.edit_text(
        "10-qadam: stadion joylashgan mahalla yoki hududni tanlang.",
        reply_markup=build_location_choice_keyboard(
            local_areas,
            "superadmin_pick_local_",
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("superadmin_pick_local_"))
async def superadmin_pick_local(callback: CallbackQuery, state: FSMContext):
    local_area_id = int(callback.data.split("_")[-1])

    await state.update_data(local_area_id=local_area_id)
    await state.set_state(AdminPanelFlow.waiting_stadium_location)
    await callback.message.answer(
        "11-qadam: stadion lokatsiyasini yuboring.",
        reply_markup=build_location_share_keyboard(),
    )
    await callback.answer()


@router.message(AdminPanelFlow.waiting_stadium_location, F.location)
async def superadmin_stadium_location(message: Message, state: FSMContext):
    state_data = await state.get_data()
    payload = {
        "name": state_data["stadium_name"],
        "address": state_data["stadium_address"],
        "phone": state_data["stadium_phone"],
        "field_size": state_data["stadium_field_size"],
        "condition_score": state_data["stadium_condition_score"],
        "amenities": state_data["stadium_amenities"],
        "price_per_hour": state_data["stadium_price"],
        "local_area_id": state_data["local_area_id"],
        "lat": message.location.latitude,
        "long": message.location.longitude,
    }

    try:
        result = await create_stadium(message.from_user.id, payload)
    except httpx.HTTPStatusError as exc:
        await message.answer(
            f"❌ {extract_error_detail(exc, 'Stadion qo`shib bo`lmadi.')}",
            reply_markup=build_location_share_keyboard(),
        )
        return

    stadium_data = result.get("data", {})
    await state.clear()
    await message.answer(
        f"✅ <b>{stadium_data.get('name', 'Stadion')}</b> muvaffaqiyatli qo'shildi.",
        reply_markup=await get_main_menu_for_user(message.from_user.id),
        parse_mode="HTML",
    )
    await render_admin_panel_message(message, message.from_user.id)


@router.message(AdminPanelFlow.waiting_stadium_location)
async def superadmin_stadium_location_wrong_input(message: Message):
    await message.answer(
        "❌ Iltimos, lokatsiyani yuboring yoki bekor qiling.",
        reply_markup=build_location_share_keyboard(),
    )


@router.message(AdminPanelFlow.choosing_stadium_field_size)
async def superadmin_stadium_field_size_wrong_input(message: Message):
    await message.answer("❌ Iltimos, maydon o'lchamini tugmalar orqali tanlang.")


@router.message(StateFilter(*STADIUM_LOCATION_STATES))
async def superadmin_stadium_location_choice_wrong_input(message: Message):
    await message.answer("❌ Iltimos, hududni tugmalar orqali tanlang.")


@router.callback_query(F.data == "superadmin_assign_start")
async def superadmin_assign_start(callback: CallbackQuery):
    try:
        profile = await require_superadmin(callback.from_user.id)
        if not profile:
            await callback.answer(SUPERADMIN_ONLY_TEXT, show_alert=True)
            return

        stadiums = await fetch_managed_stadiums(callback.from_user.id)
    except httpx.HTTPStatusError:
        await callback.answer(
            "Stadionlarni yuklab bo'lmadi.",
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        "➕ <b>Admin tayinlash</b>\n\nQaysi stadionga admin biriktirmoqchisiz?",
        reply_markup=build_stadium_selection_keyboard(
            stadiums,
            "superadmin_assign_pick_",
        ),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("superadmin_assign_pick_"))
async def superadmin_assign_pick(callback: CallbackQuery, state: FSMContext):
    stadium_id = callback.data.split("_")[-1]
    stadium = managed_stadium_cache.get(stadium_id)

    if not stadium:
        await callback.answer(
            "Stadion topilmadi.",
            show_alert=True,
        )
        return

    await state.set_state(AdminPanelFlow.waiting_admin_phone)
    await state.update_data(
        assign_stadium_id=int(stadium_id),
        assign_stadium_name=stadium["name"],
    )

    await callback.message.answer(
        f"📞 <b>{stadium['name']}</b> uchun admin telefon raqamini yuboring.\n\n"
        "Namuna: <code>998901234567</code>",
        reply_markup=build_inline_cancel_keyboard("superadmin_cancel_assign"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "superadmin_cancel_assign")
async def superadmin_cancel_assign(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await render_admin_panel_message(callback.message, callback.from_user.id, edit=True)
    await callback.answer("Admin tayinlash bekor qilindi.")


@router.message(AdminPanelFlow.waiting_admin_phone)
async def superadmin_assign_phone(message: Message, state: FSMContext):
    state_data = await state.get_data()
    stadium_id = state_data.get("assign_stadium_id")
    stadium_name = state_data.get("assign_stadium_name", "Stadion")

    if not stadium_id:
        await state.clear()
        await message.answer("❌ Tayinlash jarayonida xatolik bo'ldi. Qaytadan urinib ko'ring.")
        return

    phone = parse_phone_input(message)
    if not phone:
        await message.answer("❌ Telefon raqam yuboring.")
        return

    try:
        await assign_stadium_admin(
            message.from_user.id,
            stadium_id,
            phone,
        )
    except httpx.HTTPStatusError as exc:
        await message.answer(f"❌ {extract_error_detail(exc, 'Admin tayinlab bo`lmadi.')}")
        return

    await state.clear()
    await message.answer(
        f"✅ <b>{stadium_name}</b> uchun admin muvaffaqiyatli tayinlandi.",
        reply_markup=await get_main_menu_for_user(message.from_user.id),
        parse_mode="HTML",
    )

    try:
        admins = await fetch_stadium_admins(message.from_user.id, stadium_id)
        stadium = managed_stadium_cache.get(str(stadium_id), {"name": stadium_name})
        await message.answer(
            build_stadium_admins_text(stadium, admins),
            reply_markup=build_stadium_admins_keyboard(stadium_id, admins),
            parse_mode="HTML",
        )
    except httpx.HTTPStatusError:
        pass


@router.callback_query(F.data == "superadmin_manage_start")
async def superadmin_manage_start(callback: CallbackQuery):
    try:
        profile = await require_superadmin(callback.from_user.id)
        if not profile:
            await callback.answer(SUPERADMIN_ONLY_TEXT, show_alert=True)
            return

        stadiums = await fetch_managed_stadiums(callback.from_user.id)
    except httpx.HTTPStatusError:
        await callback.answer(
            "Stadionlarni yuklab bo'lmadi.",
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        "👥 <b>Adminlarni boshqarish</b>\n\nQaysi stadion adminlarini ko'rmoqchisiz?",
        reply_markup=build_stadium_selection_keyboard(
            stadiums,
            "superadmin_manage_pick_",
        ),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("superadmin_manage_pick_"))
async def superadmin_manage_pick(callback: CallbackQuery):
    stadium_id = callback.data.split("_")[-1]
    stadium = managed_stadium_cache.get(stadium_id)

    if not stadium:
        await callback.answer(
            "Stadion topilmadi.",
            show_alert=True,
        )
        return

    try:
        admins = await fetch_stadium_admins(callback.from_user.id, int(stadium_id))
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        if status_code == 403:
            await callback.answer(
                SUPERADMIN_ONLY_TEXT,
                show_alert=True,
            )
            return
        await callback.answer(
            "Adminlar ro'yxatini yuklab bo'lmadi.",
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        build_stadium_admins_text(stadium, admins),
        reply_markup=build_stadium_admins_keyboard(int(stadium_id), admins),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("superadmin_remove_"))
async def superadmin_remove_admin_handler(callback: CallbackQuery):
    _, _, stadium_admin_id, stadium_id = callback.data.split("_", 3)

    try:
        await remove_stadium_admin(callback.from_user.id, int(stadium_admin_id))
        admins = await fetch_stadium_admins(callback.from_user.id, int(stadium_id))
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        if status_code == 403:
            await callback.answer(
                "Bu amal faqat superadmin uchun.",
                show_alert=True,
            )
            return
        await callback.answer(
            extract_error_detail(exc, "Adminni olib tashlab bo'lmadi."),
            show_alert=True,
        )
        return

    stadium = managed_stadium_cache.get(stadium_id)
    if not stadium:
        await callback.answer(
            "Admin olib tashlandi, lekin stadion ma'lumotini topib bo'lmadi.",
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        build_stadium_admins_text(stadium, admins),
        reply_markup=build_stadium_admins_keyboard(int(stadium_id), admins),
        parse_mode="HTML",
    )
    await callback.answer("Admin olib tashlandi.")


@router.callback_query(F.data.startswith("admin_approve_"))
async def admin_approve_booking_handler(callback: CallbackQuery):
    _, _, booking_id, stadium_id, context = callback.data.split("_", 4)

    booking_to_approve = None
    try:
        if context == "today":
            bookings_before = await fetch_admin_bookings(
                callback.from_user.id,
                booking_date=date.today().isoformat(),
            )
        else:
            bookings_before = await fetch_admin_bookings(
                callback.from_user.id,
                stadium_id=int(stadium_id),
                booking_date=context,
            )

        booking_to_approve = next(
            (item for item in bookings_before if item["id"] == int(booking_id)),
            None,
        )

        await approve_admin_booking(callback.from_user.id, int(booking_id))

        if context == "today":
            bookings = await fetch_admin_bookings(
                callback.from_user.id,
                booking_date=date.today().isoformat(),
            )
        else:
            bookings = await fetch_admin_bookings(
                callback.from_user.id,
                stadium_id=int(stadium_id),
                booking_date=context,
            )
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        if status_code == 403:
            await callback.answer(
                "Siz bu bronni tasdiqlay olmaysiz.",
                show_alert=True,
            )
            return
        await callback.answer(
            extract_error_detail(exc, "Bronni tasdiqlab bo'lmadi."),
            show_alert=True,
        )
        return

    if context == "today":
        await callback.message.edit_text(
            build_today_bookings_text(bookings),
            reply_markup=build_today_bookings_keyboard(bookings),
            parse_mode="HTML",
        )
    else:
        stadium = managed_stadium_cache.get(stadium_id)
        if not stadium:
            await callback.answer(
                "Bron tasdiqlandi, lekin stadion ma'lumotini topib bo'lmadi.",
                show_alert=True,
            )
            return

        await callback.message.edit_text(
            build_admin_bookings_text(stadium, context, bookings),
            reply_markup=build_admin_bookings_keyboard(
                int(stadium_id),
                context,
                bookings,
            ),
            parse_mode="HTML",
        )

    if booking_to_approve is not None:
        await send_booking_status_notification(
            callback,
            booking_to_approve,
            "approved",
        )

    await callback.answer("Bron tasdiqlandi.")


@router.callback_query(F.data.startswith("admin_cancel_"))
async def admin_cancel_booking_handler(callback: CallbackQuery):
    _, _, booking_id, stadium_id, context = callback.data.split("_", 4)

    booking_to_cancel = None
    try:
        if context == "today":
            bookings_before = await fetch_admin_bookings(
                callback.from_user.id,
                booking_date=date.today().isoformat(),
            )
        else:
            bookings_before = await fetch_admin_bookings(
                callback.from_user.id,
                stadium_id=int(stadium_id),
                booking_date=context,
            )

        booking_to_cancel = next(
            (item for item in bookings_before if item["id"] == int(booking_id)),
            None,
        )

        await cancel_admin_booking(callback.from_user.id, int(booking_id))

        if context == "today":
            bookings = await fetch_admin_bookings(
                callback.from_user.id,
                booking_date=date.today().isoformat(),
            )
        else:
            bookings = await fetch_admin_bookings(
                callback.from_user.id,
                stadium_id=int(stadium_id),
                booking_date=context,
            )
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        if status_code == 403:
            await callback.answer(
                "Siz bu bronni bekor qila olmaysiz.",
                show_alert=True,
            )
            return
        await callback.answer(
            extract_error_detail(exc, "Bronni bekor qilib bo'lmadi."),
            show_alert=True,
        )
        return

    if context == "today":
        await callback.message.edit_text(
            build_today_bookings_text(bookings),
            reply_markup=build_today_bookings_keyboard(bookings),
            parse_mode="HTML",
        )
    else:
        stadium = managed_stadium_cache.get(stadium_id)
        if not stadium:
            await callback.answer(
                "Bron bekor qilindi, lekin stadion ma'lumotini topib bo'lmadi.",
                show_alert=True,
            )
            return

        await callback.message.edit_text(
            build_admin_bookings_text(stadium, context, bookings),
            reply_markup=build_admin_bookings_keyboard(
                int(stadium_id),
                context,
                bookings,
            ),
            parse_mode="HTML",
        )

    notification_action = "cancelled"
    if booking_to_cancel is not None:
        if normalize_booking_status(booking_to_cancel.get("status")) == "pending":
            notification_action = "rejected"
        await send_booking_status_notification(
            callback,
            booking_to_cancel,
            notification_action,
        )

    await callback.answer(
        "So'rov rad etildi." if notification_action == "rejected" else "Bron bekor qilindi."
    )
