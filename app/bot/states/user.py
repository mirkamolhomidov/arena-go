from aiogram.fsm.state import StatesGroup, State

class RegisterUser(StatesGroup):
    choosing_region = State()
    choosing_district = State()
    choosing_local_area = State()
    waiting_phone = State()

class StadiumSearch(StatesGroup):
    """Stadion qidirish uchun state"""
    waiting_location = State()


class BookingFlow(StatesGroup):
    choosing_date = State()
    waiting_time_range = State()


class AdminPanelFlow(StatesGroup):
    waiting_admin_phone = State()
    waiting_superadmin_phone = State()
    waiting_stadium_name = State()
    waiting_stadium_address = State()
    waiting_stadium_phone = State()
    waiting_stadium_price = State()
    waiting_stadium_start_time = State()
    waiting_stadium_end_time = State()
    choosing_stadium_region = State()
    choosing_stadium_district = State()
    choosing_stadium_local_area = State()
    waiting_stadium_location = State()
