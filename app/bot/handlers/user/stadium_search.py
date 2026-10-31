import httpx
import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from app.bot.handlers.user.stadium_common import (
    format_amenities,
    format_condition_score,
    format_field_size,
    format_price,
    search_results_cache,
    stadium_cache,
)
from app.bot.keyboards.main_menu import (
    get_location_request_keyboard,
    get_main_menu_for_user,
)
from app.bot.states.user import StadiumSearch
from app.core.config import settings

router = Router()


def parse_distance(distance_str):
    """
    Parse distance string like '73 metr', '1.5 km', etc.
    Returns distance in kilometers as float.
    """
    if isinstance(distance_str, (int, float)):
        return float(distance_str)
    
    if not isinstance(distance_str, str):
        return 0.0
    
    normalized = distance_str.lower().replace(',', '.').strip()

    total_km = 0.0
    km_match = re.search(r'([\d.]+)\s*km\b', normalized)
    meter_match = re.search(r'([\d.]+)\s*(metr|meter|m)\b', normalized)

    if km_match:
        total_km += float(km_match.group(1))

    if meter_match:
        total_km += float(meter_match.group(1)) / 1000

    if km_match or meter_match:
        return total_km

    match = re.search(r'[\d.]+', normalized)
    if not match:
        return 0.0

    return float(match.group())


def get_distance_km(stadium):
    """Prefer backend numeric distance if available, otherwise parse string."""
    distance_meters = stadium.get('distance_meters')
    if isinstance(distance_meters, (int, float)):
        return float(distance_meters) / 1000

    return parse_distance(stadium.get('distance', '0'))


def has_distance_info(stadium) -> bool:
    return stadium.get("distance_meters") is not None or stadium.get("distance") is not None


def build_stadium_list_message(stadiums):
    """Stadionlar ro'yxati uchun xabar va keyboard yaratish"""
    text = "🏟 <b>Sizga eng yaqin stadionlar:</b>\n\n"
    keyboard_buttons = []

    for idx, stadium in enumerate(stadiums, 1):
        stadium["_list_source"] = "search"
        name = stadium.get('name', 'Noma\'lum stadion')
        address = stadium.get('address', 'Manzil ko\'rsatilmagan')
        phone = stadium.get('phone', 'Telefon yo\'q')
        field_size = format_field_size(stadium.get('field_size'))
        condition_score = format_condition_score(stadium.get('condition_score'))
        stadium_id = stadium.get('id') or stadium.get('stadium_id') or idx

        # Stadion ma'lumotlarini cache ga saqlash
        stadium_cache[str(stadium_id)] = stadium

        # Parse distance safely
        distance = get_distance_km(stadium)

        # Emoji tanlash
        emoji = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉"

        # Display distance based on value
        if distance < 1:
            distance_text = f"{distance * 1000:.0f} metr"
        else:
            distance_text = f"{distance:.2f} km"

        text += f"{emoji} <b>{idx}. {name}</b>\n"
        text += f"   📏 Masofa: <code>{distance_text}</code>\n"
        text += f"   👥 Maydon: {field_size}\n"
        text += f"   ⭐️ Holati: {condition_score}\n"
        text += f"   🏠 {address}\n"
        text += f"   📞 {phone}\n\n"

        # Button text with shorter distance format
        if distance < 1:
            btn_distance = f"{distance * 1000:.0f}m"
        else:
            btn_distance = f"{distance:.1f}km"

        # Har bir stadion uchun tugma
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{emoji} {name} - {btn_distance}",
                callback_data=f"stadium_detail_{stadium_id}"
            )
        ])

    # Qo'shimcha tugmalar
    keyboard_buttons.append([
        InlineKeyboardButton(
            text="🔄 Qayta qidirish",
            callback_data="search_again"
        )
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    return text, keyboard


@router.message(F.text == "📍 Stadion topish")
async def stadium_search_start(message: Message, state: FSMContext):
    """Stadion qidirish boshlash - lokatsiya so'rash"""
    await state.set_state(StadiumSearch.waiting_location)
    await message.answer(
        "🏟 <b>Yaqin atrofdagi stadionlarni topish</b>\n\n"
        "📍 Iltimos, lokatsiyangizni yuboring.\n"
        "Biz sizga eng yaqin 3 ta stadionni ko'rsatamiz.",
        reply_markup=get_location_request_keyboard(),
        parse_mode="HTML"
    )


@router.message(StadiumSearch.waiting_location, F.location)
async def process_location(message: Message, state: FSMContext):
    """Lokatsiyani qabul qilib, backendga yuborish"""
    lat = message.location.latitude
    long = message.location.longitude

    # Loading xabari
    loading_msg = await message.answer(
        "🔍 Yaqin atrofdagi stadionlar qidirilmoqda...",
        reply_markup=await get_main_menu_for_user(message.from_user.id)
    )

    async with httpx.AsyncClient() as client:
        try:
            # Backend API ga so'rov yuborish
            response = await client.get(
                f"{settings.BASE_URL}/stadiums/nearest",
                params={
                    "lat": lat,
                    "long": long
                },
                timeout=15.0
            )

            if response.status_code == 200:
                stadiums = response.json()

                # Agar stadion topilmasa
                if not stadiums or len(stadiums) == 0:
                    try:
                        await loading_msg.edit_text(
                            "❌ Afsuski, yaqin atrofda stadion topilmadi.\n\n"
                            "Iltimos, boshqa joydan urinib ko'ring.",
                        )
                    except Exception:
                        await message.answer(
                            "❌ Afsuski, yaqin atrofda stadion topilmadi.\n\n"
                            "Iltimos, boshqa joydan urinib ko'ring.",
                        )
                    await state.clear()
                    return

                # Faqat birinchi 3 ta stadionni olamiz
                top_3_stadiums = stadiums[:3]
                
                # User uchun qidiruv natijalarini saqlash
                user_id = message.from_user.id
                search_results_cache[user_id] = top_3_stadiums

                # Xabar va keyboard yaratish
                text, keyboard = build_stadium_list_message(top_3_stadiums)

                # Natijani ko'rsatish
                try:
                    await loading_msg.edit_text(
                        text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                except Exception:
                    # If edit fails, send new message
                    await message.answer(
                        text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )

                await state.clear()

            elif response.status_code == 404:
                try:
                    await loading_msg.edit_text(
                        "❌ Stadionlar topilmadi.\n\n"
                        "Iltimos, boshqa joydan urinib ko'ring."
                    )
                except Exception:
                    await message.answer(
                        "❌ Stadionlar topilmadi.\n\n"
                        "Iltimos, boshqa joydan urinib ko'ring."
                    )
                await state.clear()

            else:
                try:
                    await loading_msg.edit_text(
                        f"❌ Xatolik yuz berdi (Kod: {response.status_code})\n\n"
                        "Iltimos, qaytadan urinib ko'ring."
                    )
                except Exception:
                    await message.answer(
                        f"❌ Xatolik yuz berdi (Kod: {response.status_code})\n\n"
                        "Iltimos, qaytadan urinib ko'ring."
                    )
                await state.clear()

        except httpx.TimeoutException:
            try:
                await loading_msg.edit_text(
                    "⏱ Server uzoq vaqt javob bermadi.\n\n"
                    "Iltimos, qaytadan urinib ko'ring."
                )
            except Exception:
                await message.answer(
                    "⏱ Server uzoq vaqt javob bermadi.\n\n"
                    "Iltimos, qaytadan urinib ko'ring."
                )
            await state.clear()

        except httpx.ConnectError:
            try:
                await loading_msg.edit_text(
                    "❌ Serverga ulanib bo'lmadi.\n\n"
                    "Internet aloqangizni tekshiring yoki keyinroq urinib ko'ring."
                )
            except Exception:
                await message.answer(
                    "❌ Serverga ulanib bo'lmadi.\n\n"
                    "Internet aloqangizni tekshiring yoki keyinroq urinib ko'ring."
                )
            await state.clear()

        except Exception as e:
            try:
                await loading_msg.edit_text(
                    f"❌ Kutilmagan xatolik yuz berdi:\n"
                    f"<code>{str(e)}</code>\n\n"
                    "Iltimos, qaytadan urinib ko'ring.",
                    parse_mode="HTML"
                )
            except Exception:
                await message.answer(
                    f"❌ Kutilmagan xatolik yuz berdi:\n"
                    f"<code>{str(e)}</code>\n\n"
                    "Iltimos, qaytadan urinib ko'ring.",
                    parse_mode="HTML"
                )
            await state.clear()


@router.callback_query(F.data.startswith("stadium_detail_"))
async def show_stadium_detail(callback: CallbackQuery):
    """Stadion tafsilotlarini ko'rsatish"""
    stadium_id = callback.data.split("_")[-1]
    
    # Cache dan stadion ma'lumotlarini olish
    stadium = stadium_cache.get(stadium_id)
    
    if not stadium:
        await callback.answer(
            "❌ Stadion ma'lumotlari topilmadi. Qayta qidiring.",
            show_alert=True
        )
        return

    # Ma'lumotlarni olish
    name = stadium.get('name', 'Noma\'lum stadion')
    address = stadium.get('address', 'Manzil ko\'rsatilmagan')
    phone = stadium.get('phone', 'Telefon yo\'q')
    field_size = format_field_size(stadium.get('field_size'))
    condition_score = format_condition_score(stadium.get('condition_score'))
    amenities = format_amenities(stadium.get('amenities'))
    price = stadium.get('price_per_hour', 0)
    local_area = stadium.get('local_area', '-')
    location_url = stadium.get('location_url', '')

    distance_line = ""
    if has_distance_info(stadium):
        distance = get_distance_km(stadium)
        if distance < 1:
            distance_text = f"{distance * 1000:.0f} metr"
        else:
            distance_text = f"{distance:.2f} km"

        distance_line = f"📏 Masofa: <code>{distance_text}</code>\n"

    condition_suffix = " ✅" if stadium.get('condition_score') is not None else ""

    # Tafsilotli xabar
    detail_text = (
        f"🏟 <b>{name}</b>\n\n"
        f"{distance_line}"
        f"🏠 Manzil: {address}\n"
        f"📍 Hudud: {local_area}\n"
        f"📞 Telefon: {phone}\n"
        f"👥 Maydon o'lchami: {field_size}\n"
        f"⭐️ Stadion holati: {condition_score}{condition_suffix}\n"
        f"💰 Narx: {format_price(price)} so'm/soat\n"
        f"💡 Qulayliklar: {amenities}"
    )

    # Tugmalar
    keyboard_buttons = []
    back_callback = (
        "back_to_local_stadiums"
        if stadium.get("_list_source") == "home"
        else "back_to_results"
    )
    
    # Agar location_url mavjud bo'lsa, xaritada ko'rish tugmasi
    if location_url:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text="🗺 Xaritada ko'rish",
                url=location_url
            )
        ])
    
    keyboard_buttons.extend([
        [
            InlineKeyboardButton(
                text="📅 Bron qilish",
                callback_data=f"book_stadium_{stadium_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Orqaga",
                callback_data=back_callback
            )
        ]
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.edit_text(
        detail_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data == "search_again")
async def search_again(callback: CallbackQuery, state: FSMContext):
    """Qayta qidirish"""
    await callback.message.delete()
    await state.set_state(StadiumSearch.waiting_location)

    await callback.message.answer(
        "🏟 <b>Yaqin atrofdagi stadionlarni topish</b>\n\n"
        "📍 Iltimos, lokatsiyangizni yuboring.\n"
        "Biz sizga eng yaqin 3 ta stadionni ko'rsatamiz.",
        reply_markup=get_location_request_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data == "back_to_results")
async def back_to_results(callback: CallbackQuery):
    """Natijalarga qaytish"""
    user_id = callback.from_user.id
    
    # User qidiruv natijalarini olish
    stadiums = search_results_cache.get(user_id)
    
    if not stadiums:
        await callback.answer(
            "❗️ Yangi qidiruv uchun 'Qayta qidirish' tugmasini bosing.",
            show_alert=True
        )
        return
    
    # Xabar va keyboard yaratish
    text, keyboard = build_stadium_list_message(stadiums)
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception:
        # Agar edit ishlamasa, yangi xabar yuborish
        await callback.message.answer(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    await callback.answer()


@router.message(StadiumSearch.waiting_location, F.text == "◀️ Orqaga")
async def cancel_search(message: Message, state: FSMContext):
    """Qidiruvni bekor qilish"""
    await state.clear()
    await message.answer(
        "🏠 Asosiy menyu",
        reply_markup=await get_main_menu_for_user(message.from_user.id)
    )


@router.message(StadiumSearch.waiting_location)
async def wrong_input(message: Message):
    """Noto'g'ri ma'lumot yuborilsa"""
    await message.answer(
        "❌ Iltimos, faqat lokatsiya yuboring!\n\n"
        "📍 'Lokatsiyamni yuborish' tugmasini bosing.",
        reply_markup=get_location_request_keyboard()
    )
