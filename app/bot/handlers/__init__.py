from aiogram import Dispatcher
from .user import start

def register_handlers(dp: Dispatcher):
    dp.include_router(start.router)
