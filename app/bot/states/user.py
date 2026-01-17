from aiogram.fsm.state import StatesGroup, State

class RegisterUser(StatesGroup):
    choosing_region = State()
    choosing_district = State()
    choosing_local_area = State()
    waiting_phone = State()

class StadiumSearch(StatesGroup):
    """Stadion qidirish uchun state"""
    waiting_location = State()