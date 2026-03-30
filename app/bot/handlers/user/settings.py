"""Handle user settings flows inside the Telegram bot."""

import aiohttp
from aiogram import F, Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.keyboards.phone import phone_keyboard
from app.bot.states.user import RegisterUser
from app.core.config import settings


settings_router = Router()
API_BASE = settings.BASE_URL


async def fetch_user_profile(telegram_id: int) -> dict | None:
    """Fetch the current Telegram user's profile from the API."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE}/users/{telegram_id}") as resp:
            if resp.status != 200:
                return None
            return await resp.json()


async def fetch_local_area_name(local_area_id: int | None) -> str:
    """Resolve a local area name for settings display."""
    if not local_area_id:
        return "-"

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{API_BASE}/locations/local-areas",
            params={"local_area_id": local_area_id},
        ) as resp:
            if resp.status != 200:
                return str(local_area_id)

            payload = await resp.json()
            if not payload:
                return str(local_area_id)

            return payload[0].get("name", str(local_area_id))


def build_settings_keyboard() -> InlineKeyboardMarkup:
    """Build the inline keyboard for the settings menu."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👤 Profilni yangilash",
                    callback_data="settings_profile",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📱 Telefonni o'zgartirish",
                    callback_data="settings_change_phone",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏘 Hududni o'zgartirish",
                    callback_data="settings_change_area",
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Yopish",
                    callback_data="settings_close",
                )
            ],
        ]
    )


def format_role(role: str | None) -> str:
    """Convert stored role values into a user-friendly label."""
    mapping = {
        "user": "Foydalanuvchi",
        "admin": "Admin",
        "superadmin": "Superadmin",
    }
    return mapping.get(role or "", role or "-")


async def render_settings_text(telegram_id: int) -> str | None:
    """Build the settings summary text for the current user."""
    user = await fetch_user_profile(telegram_id)
    if not user:
        return None

    local_area_name = await fetch_local_area_name(user.get("local_area_id"))
    username = user.get("username")
    username_text = f"@{username}" if username else "-"

    return (
        "⚙️ <b>Sozlamalar</b>\n\n"
        f"👤 Ism: {user.get('first_name') or '-'}\n"
        f"🪪 Username: {username_text}\n"
        f"📱 Telefon: {user.get('phone') or '-'}\n"
        f"🏘 Hudud: {local_area_name}\n"
        f"🛡 Role: {format_role(user.get('role'))}\n\n"
        "Kerakli bo'limni tanlang:"
    )


async def update_settings_message(
    callback: types.CallbackQuery,
    text: str,
) -> None:
    """Safely refresh the settings panel without failing on identical content."""
    try:
        await callback.message.edit_text(
            text,
            reply_markup=build_settings_keyboard(),
            parse_mode="HTML",
        )
    except TelegramBadRequest as error:
        if "message is not modified" not in str(error).lower():
            raise


async def send_region_picker(message: types.Message):
    """Send the region selection keyboard for location updates."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE}/locations/regions") as resp:
            regions = await resp.json()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=item["name"], callback_data=f"region_{item['id']}")]
            for item in regions
        ]
    )

    await message.answer(
        "🏘 Yangi hududni tanlash uchun viloyatni belgilang:",
        reply_markup=keyboard,
    )


@settings_router.message(F.text == "⚙️ Sozlamalar")
async def settings_menu(message: types.Message, state: FSMContext):
    """Open the settings summary screen."""
    await state.clear()
    text = await render_settings_text(message.from_user.id)

    if not text:
        await message.answer(
            "❌ Profil topilmadi. Avval /start orqali ro'yxatdan o'ting."
        )
        return

    await message.answer(
        text,
        reply_markup=build_settings_keyboard(),
        parse_mode="HTML",
    )


@settings_router.callback_query(F.data == "settings_profile")
async def settings_profile(callback: types.CallbackQuery):
    """Refresh and show the current settings summary."""
    text = await render_settings_text(callback.from_user.id)
    if not text:
        await callback.answer(
            "Profil ma'lumotini olib bo'lmadi.",
            show_alert=True,
        )
        return

    await update_settings_message(callback, text)
    await callback.answer("Profil yangilandi")


@settings_router.callback_query(F.data == "settings_change_phone")
async def settings_change_phone(callback: types.CallbackQuery, state: FSMContext):
    """Start the phone update flow using the existing contact handler."""
    user = await fetch_user_profile(callback.from_user.id)
    if not user:
        await callback.answer(
            "Profil topilmadi.",
            show_alert=True,
        )
        return

    await state.clear()
    await state.update_data(
        flow_type="settings_change_phone",
        first_name=user.get("first_name"),
        username=user.get("username"),
        telegram_id=user.get("telegram_id"),
        local_area_id=user.get("local_area_id"),
    )
    await state.set_state(RegisterUser.waiting_phone)

    await callback.message.answer(
        "📱 Yangi telefon raqamingizni yuboring:",
        reply_markup=phone_keyboard,
    )
    await callback.answer()


@settings_router.callback_query(F.data == "settings_change_area")
async def settings_change_area(callback: types.CallbackQuery, state: FSMContext):
    """Start the local-area update flow using the existing location picker."""
    user = await fetch_user_profile(callback.from_user.id)
    if not user:
        await callback.answer(
            "Profil topilmadi.",
            show_alert=True,
        )
        return

    await state.clear()
    await state.update_data(
        flow_type="settings_change_area",
        first_name=user.get("first_name"),
        username=user.get("username"),
        telegram_id=user.get("telegram_id"),
        phone=user.get("phone"),
        local_area_id=user.get("local_area_id"),
    )
    await state.set_state(RegisterUser.choosing_region)

    await send_region_picker(callback.message)
    await callback.answer()


@settings_router.callback_query(F.data == "settings_close")
async def settings_close(callback: types.CallbackQuery):
    """Close the inline settings panel."""
    await callback.message.edit_text("⚙️ Sozlamalar yopildi.")
    await callback.answer()
