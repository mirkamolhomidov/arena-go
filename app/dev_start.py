"""Run the Telegram bot in polling mode for local development."""

import asyncio
from app.bot.dispatcher import bot, dp
from app.bot.handlers import register_handlers
from app.core.logger import get_logger, setup_logging


setup_logging()
logger = get_logger(__name__)

async def main():
    """Start the polling worker with registered bot handlers."""
    register_handlers(dp)
    logger.info("Bot polling started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
