import aiohttp
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from app.bot.keyboards.main_menu import get_main_menu_for_user
from app.bot.states.user import RegisterUser
from app.core.config import settings

location_router = Router()
API_BASE = settings.BASE_URL


async def update_user_profile(state: FSMContext):
    """Persist updated registration or settings data through the users API."""
    data = await state.get_data()
    payload = {
        "first_name": data["first_name"],
        "username": data["username"],
        "telegram_id": data["telegram_id"],
        "phone": data["phone"],
        "local_area_id": data["local_area_id"],
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_BASE}/users/create", json=payload) as resp:
            return resp.status


@location_router.callback_query(F.data.startswith("region_"))
async def region_selected(callback: types.CallbackQuery, state: FSMContext):
    """Viloyat tanlanganda"""
    region_id = int(callback.data.split("_")[1])
    await state.update_data(region_id=region_id)

    # Eski xabarni o'chirish
    try:
        await callback.message.delete()
    except Exception:
        pass

    # Districtlarni olish
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE}/locations/districts", params={"region_id": region_id}) as resp:
            districts = await resp.json()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=d["name"], callback_data=f"district_{d['id']}")]
            for d in districts
        ]
    )

    # Yangi xabar yuborish
    await callback.message.answer(
        "📍 Tumanni tanlang:",
        reply_markup=keyboard
    )
    
    await state.set_state(RegisterUser.choosing_district)
    await callback.answer()


@location_router.callback_query(F.data.startswith("district_"))
async def district_selected(callback: types.CallbackQuery, state: FSMContext):
    """Tuman tanlanganda"""
    district_id = int(callback.data.split("_")[1])
    await state.update_data(district_id=district_id)

    # Eski xabarni o'chirish
    try:
        await callback.message.delete()
    except Exception:
        pass

    # Local areasni olish
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE}/locations/local-areas", params={"district_id": district_id}) as resp:
            locals_ = await resp.json()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=l["name"], callback_data=f"local_{l['id']}")]
            for l in locals_
        ]
    )

    # Yangi xabar yuborish
    await callback.message.answer(
        "🏘 Qishloqni tanlang:",
        reply_markup=keyboard
    )
    
    await state.set_state(RegisterUser.choosing_local_area)
    await callback.answer()


@location_router.callback_query(F.data.startswith("local_"))
async def local_selected(callback: types.CallbackQuery, state: FSMContext):
    """Mahalla/qishloq tanlanganda"""
    local_area_id = int(callback.data.split("_")[1])
    await state.update_data(local_area_id=local_area_id)
    state_data = await state.get_data()

    # Eski xabarni o'chirish
    try:
        await callback.message.delete()
    except Exception:
        pass

    if state_data.get("flow_type") == "settings_change_area":
        status = await update_user_profile(state)
        if status == 200:
            from app.bot.handlers.user.booking import send_local_stadiums_overview

            await callback.message.answer(
                "✅ Hududingiz muvaffaqiyatli yangilandi.",
                reply_markup=await get_main_menu_for_user(callback.from_user.id)
            )
            await send_local_stadiums_overview(callback.message, callback.from_user.id)
        else:
            await callback.message.answer(
                "❌ Hududni yangilashda xatolik yuz berdi.",
                reply_markup=await get_main_menu_for_user(callback.from_user.id)
            )

        await state.clear()
        await callback.answer()
        return

    from app.bot.keyboards.phone import phone_keyboard

    # Telefon so'rash - bu xabar o'chirilmaydi
    await callback.message.answer(
        "📱 Telefon raqamingizni yuboring:",
        reply_markup=phone_keyboard
    )
    
    await state.set_state(RegisterUser.waiting_phone)
    await callback.answer()
