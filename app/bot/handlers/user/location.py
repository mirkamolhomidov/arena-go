import aiohttp
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from app.bot.states.user import RegisterUser
from app.core.config import settings

location_router = Router()
API_BASE = settings.BASE_URL


@location_router.callback_query(F.data.startswith("region_"))
async def region_selected(callback: types.CallbackQuery, state: FSMContext):
    region_id = int(callback.data.split("_")[1])
    await state.update_data(region_id=region_id)

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

    await callback.message.answer("Tumanni tanlang:", reply_markup=keyboard)
    await state.set_state(RegisterUser.choosing_district)


@location_router.callback_query(F.data.startswith("district_"))
async def district_selected(callback: types.CallbackQuery, state: FSMContext):
    district_id = int(callback.data.split("_")[1])
    await state.update_data(district_id=district_id)

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

    await callback.message.answer("Qishloqni tanlang:", reply_markup=keyboard)
    await state.set_state(RegisterUser.choosing_local_area)


@location_router.callback_query(F.data.startswith("local_"))
async def local_selected(callback: types.CallbackQuery, state: FSMContext):
    local_area_id = int(callback.data.split("_")[1])
    await state.update_data(local_area_id=local_area_id)

    from app.bot.keyboards.phone import phone_keyboard

    await callback.message.answer(
        "📱 Telefon raqamingizni yuboring:",
        reply_markup=phone_keyboard
    )
    await state.set_state(RegisterUser.waiting_phone)
