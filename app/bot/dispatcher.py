from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from app.core.config import settings
from app.bot.handlers.user.start import router
from app.bot.handlers.user.location import location_router
from app.bot.handlers.user.phone import phone_router

bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher()
