from aiogram import Dispatcher

from app.bot.handlers.admin import panel
from app.bot.handlers.user import booking, stadium_search
from .user import start, location, phone, settings

def register_handlers(dp: Dispatcher):
    dp.include_router(start.router)
    dp.include_router(settings.settings_router)
    dp.include_router(location.location_router)
    dp.include_router(phone.phone_router)
    dp.include_router(panel.router)
    dp.include_router(booking.router)
    dp.include_router(stadium_search.router)
