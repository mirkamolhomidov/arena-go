import aiohttp
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from app.bot.handlers.user.booking import send_local_stadiums_overview
from app.bot.states.user import RegisterUser
from app.bot.keyboards.main_menu import get_main_menu, get_main_menu_for_user
from app.core.config import settings

phone_router = Router()
API_URL = f"{settings.BASE_URL}/users/create"


@phone_router.message(RegisterUser.waiting_phone, F.contact)
async def phone_handler(message: types.Message, state: FSMContext):
    contact = message.contact

    if contact.user_id != message.from_user.id:
        await message.answer("❌ Iltimos, o'zingizning raqamingizni yuboring")
        return

    await state.update_data(phone=contact.phone_number)
    data = await state.get_data()
    flow_type = data.get("flow_type")

    payload = {
        "first_name": data["first_name"],
        "username": data["username"],
        "telegram_id": data["telegram_id"],
        "phone": data["phone"],
        "local_area_id": data["local_area_id"]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, json=payload) as resp:
            if resp.status == 200:
                if flow_type == "settings_change_phone":
                    await message.answer(
                        "✅ Telefon raqamingiz muvaffaqiyatli yangilandi.",
                        reply_markup=await get_main_menu_for_user(message.from_user.id)
                    )
                else:
                    await message.answer(
                        "✅ Tabriklaymiz! Ro'yxatdan muvaffaqiyatli o'tdingiz.\n\n"
                        "🏟 Endi siz stadionlarni qidirishingiz va bron qilishingiz mumkin!",
                        reply_markup=get_main_menu("user")
                    )
                    await send_local_stadiums_overview(message, data["telegram_id"])
                await state.clear()
            else:
                await message.answer(
                    "❌ Ma'lumotni saqlashda xatolik yuz berdi.\n"
                    "Iltimos, qaytadan urinib ko'ring.",
                    reply_markup=await get_main_menu_for_user(message.from_user.id)
                )
                await state.clear()
