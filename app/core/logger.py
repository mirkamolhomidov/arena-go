"""Provide centralized application logging and Telegram error notifications."""

from __future__ import annotations

import html
import json
import logging
import queue
import threading
import urllib.parse
import urllib.request
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from app.core.config import settings


APP_LOGGER_NAME = "arena_go"
_LOGGING_READY = False


def _safe_json(data: Any) -> str:
    """Serialize context data into a readable JSON string."""
    try:
        return json.dumps(data, ensure_ascii=False, default=str)
    except Exception:
        return str(data)


class SafeExtraFormatter(logging.Formatter):
    """Format log records even when optional extra fields are missing."""

    def format(self, record: logging.LogRecord) -> str:
        """Render a log record with safe default extra values."""
        if not hasattr(record, "status_code"):
            record.status_code = "-"

        if not hasattr(record, "context_data"):
            record.context_data = "-"
        elif not isinstance(record.context_data, str):
            record.context_data = _safe_json(record.context_data)

        return super().format(record)


class TelegramErrorHandler(logging.Handler):
    """Send error-level log records to a Telegram chat in the background."""

    def __init__(self, bot_token: str, chat_id: str) -> None:
        """Create a Telegram handler with a background delivery queue."""
        super().__init__(level=logging.ERROR)
        self.bot_token = bot_token
        self.chat_id = chat_id
        self._queue: queue.Queue[str] = queue.Queue(maxsize=100)
        self._worker = threading.Thread(
            target=self._consume_queue,
            daemon=True,
            name="telegram-log-worker",
        )
        self._worker.start()

    def emit(self, record: logging.LogRecord) -> None:
        """Queue a formatted Telegram notification for an error record."""
        try:
            message = self._build_message(record)
            self._queue.put_nowait(message)
        except Exception:
            self.handleError(record)

    def _consume_queue(self) -> None:
        """Deliver queued log messages to Telegram."""
        while True:
            message = self._queue.get()
            try:
                self._send_message(message)
            except Exception:
                continue
            finally:
                self._queue.task_done()

    def _send_message(self, message: str) -> None:
        """Post a single message to the configured Telegram chat."""
        payload = urllib.parse.urlencode(
            {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": "true",
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            url=f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
            data=payload,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(request, timeout=8):
            return

    def _build_message(self, record: logging.LogRecord) -> str:
        """Build a compact Telegram-friendly error message."""
        formatter = self.formatter or logging.Formatter(
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        timestamp = formatter.formatTime(record)
        exception_text = ""

        if record.exc_info:
            exception_text = formatter.formatException(record.exc_info)

        context_data = getattr(record, "context_data", "-")
        if not isinstance(context_data, str):
            context_data = _safe_json(context_data)

        message = (
            "<b>Arena Go Error</b>\n"
            f"<b>Level:</b> {record.levelname}\n"
            f"<b>Time:</b> {html.escape(timestamp)}\n"
            f"<b>Logger:</b> {html.escape(record.name)}\n"
            f"<b>File:</b> {html.escape(record.pathname)}:{record.lineno}\n"
            f"<b>Function:</b> {html.escape(record.funcName)}\n"
            f"<b>Status:</b> {html.escape(str(getattr(record, 'status_code', '-')))}\n"
            f"<b>Message:</b> <code>{html.escape(record.getMessage())}</code>\n"
            f"<b>Context:</b> <code>{html.escape(context_data)}</code>"
        )

        if exception_text:
            message += f"\n<b>Trace:</b> <code>{html.escape(exception_text[-1800:])}</code>"

        return message[:3900]


def setup_logging() -> None:
    """Configure console, file, and Telegram logging for the app."""
    global _LOGGING_READY

    if _LOGGING_READY:
        return

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    log_path = Path(settings.LOG_FILE_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    formatter = SafeExtraFormatter(
        fmt=(
            "%(asctime)s | %(levelname)s | %(name)s | %(pathname)s:%(lineno)d "
            "| status=%(status_code)s | %(message)s | context=%(context_data)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    app_logger = logging.getLogger(APP_LOGGER_NAME)
    app_logger.setLevel(log_level)
    app_logger.handlers.clear()
    app_logger.propagate = False

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    app_logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    app_logger.addHandler(file_handler)

    if settings.ERROR_BOT_TOKEN and settings.ERROR_BOT_CHAT_ID:
        telegram_handler = TelegramErrorHandler(
            bot_token=settings.ERROR_BOT_TOKEN,
            chat_id=settings.ERROR_BOT_CHAT_ID,
        )
        telegram_handler.setFormatter(formatter)
        app_logger.addHandler(telegram_handler)

    _LOGGING_READY = True


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a child logger under the shared application logger."""
    setup_logging()
    if not name:
        return logging.getLogger(APP_LOGGER_NAME)
    return logging.getLogger(f"{APP_LOGGER_NAME}.{name}")


def log_exception(
    logger: logging.Logger,
    exception: Exception,
    *,
    context: str,
    source: str,
    status_code: int = 500,
    extra: dict[str, Any] | None = None,
    stacklevel: int = 2,
) -> None:
    """Write a structured exception log with shared context fields."""
    context_data = {
        "source": source,
        "context": context,
    }

    if extra:
        context_data.update(extra)

    logger.error(
        "%s failed: %s",
        context,
        exception,
        exc_info=(type(exception), exception, exception.__traceback__),
        extra={
            "status_code": status_code,
            "context_data": context_data,
        },
        stacklevel=stacklevel,
    )
