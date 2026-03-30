"""Create the shared bot and dispatcher instances."""

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import ErrorEvent

from app.core.error_handling import GENERIC_BOT_ERROR_MESSAGE
from app.core.config import settings
from app.core.logger import get_logger, log_exception, setup_logging


setup_logging()
logger = get_logger(__name__)

bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher()


async def handle_bot_error(event: ErrorEvent) -> bool:
    """Log unhandled bot exceptions and show a safe user message."""
    update_data = event.update.model_dump(exclude_none=True)

    log_exception(
        logger,
        event.exception,
        context="Unhandled aiogram event",
        source="bot",
        status_code=500,
        extra={"update": update_data},
    )

    try:
        if event.update.callback_query:
            await event.update.callback_query.answer(
                GENERIC_BOT_ERROR_MESSAGE,
                show_alert=True,
            )
        elif event.update.message:
            await event.update.message.answer(GENERIC_BOT_ERROR_MESSAGE)
    except Exception as notify_error:
        log_exception(
            logger,
            notify_error,
            context="Bot error fallback notification",
            source="bot",
            status_code=500,
        )

    return True


dp.errors.register(handle_bot_error)
