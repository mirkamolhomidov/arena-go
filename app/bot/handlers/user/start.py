from aiogram import F, Router, types
from aiogram.filters import CommandStart
import aiohttp
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.handlers.user.booking import send_local_stadiums_overview
from app.bot.states.user import RegisterUser
from app.bot.keyboards.main_menu import get_main_menu, get_main_menu_for_user
from app.core.config import settings

router = Router()
API_URL = settings.BASE_URL


@router.message(CommandStart())
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()

    telegram_id = message.from_user.id

    # Avval user bazada bor yoki yo'qligini tekshiramiz
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{settings.BASE_URL}/users/{telegram_id}") as resp:
            if resp.status == 200:
                # User allaqachon ro'yxatdan o'tgan
                user_data = await resp.json()
                await message.answer(
                    f"👋 Xush kelibsiz, {user_data.get('first_name', 'Foydalanuvchi')}!\n\n"
                    f"Siz allaqachon ro'yxatdan o'tgansiz.",
                    reply_markup=get_main_menu(user_data.get("role", "user"))
                )
                await send_local_stadiums_overview(message, telegram_id)
                return

    # Agar user yangi bo'lsa, ro'yxatdan o'tkazamiz
    await state.update_data(
        first_name=message.from_user.first_name,
        username=message.from_user.username,
        telegram_id=telegram_id
    )

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{settings.BASE_URL}/locations/regions") as resp:
            regions = await resp.json()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=r["name"], callback_data=f"region_{r['id']}")]
            for r in regions
        ]
    )

    await message.answer(
        "👋 Salom! ArenaGo botiga xush kelibsiz.\n\n"
        "📍 Iltimos, viloyatingizni tanlang:",
        reply_markup=keyboard
    )

    await state.set_state(RegisterUser.choosing_region)


@router.message(F.text == "/menu")
async def show_menu(message: types.Message, state: FSMContext):
    """Asosiy menyuni ko'rsatish"""
    await state.clear()
    await message.answer(
        "🏠 Asosiy menyu",
        reply_markup=await get_main_menu_for_user(message.from_user.id)
    )
