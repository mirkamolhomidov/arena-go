import aiohttp
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from app.bot.states.user import RegisterUser
from app.bot.keyboards.main_menu import get_main_menu  # Import qo'shamiz
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
                # Asosiy menyuni ko'rsatamiz
                await message.answer(
                    "✅ Tabriklaymiz! Ro'yxatdan muvaffaqiyatli o'tdingiz.\n\n"
                    "🏟 Endi siz stadionlarni qidirishingiz va bron qilishingiz mumkin!",
                    reply_markup=get_main_menu()  # Asosiy menyu
                )
                await state.clear()
            else:
                await message.answer(
                    "❌ Ro'yxatdan o'tishda xatolik yuz berdi.\n"
                    "Iltimos, qaytadan urinib ko'ring.",
                    reply_markup=get_main_menu()
                )
                await state.clear()