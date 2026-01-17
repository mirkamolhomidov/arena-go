from aiogram import Dispatcher

from app.bot.handlers.user import stadium_search
from .user import start, location, phone

def register_handlers(dp: Dispatcher):
    dp.include_router(start.router)
    dp.include_router(location.location_router)
    dp.include_router(phone.phone_router)
    dp.include_router(stadium_search.router)