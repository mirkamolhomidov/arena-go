"""Provide shared exception handling for API services and bot flows."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logger import get_logger, log_exception


GENERIC_API_ERROR_MESSAGE = (
    "Serverda vaqtinchalik xatolik yuz berdi. Keyinroq urinib ko'ring."
)
GENERIC_BOT_ERROR_MESSAGE = (
    "❌ Xatolik yuz berdi. Iltimos, birozdan keyin qayta urinib ko'ring."
)


def build_logged_http_exception(
    status_code: int = 500,
    detail: str = GENERIC_API_ERROR_MESSAGE,
) -> HTTPException:
    """Create an HTTP exception that is already logged and safe for users."""
    exception = HTTPException(status_code=status_code, detail=detail)
    setattr(exception, "_arena_logged", True)
    return exception


class ServiceErrorHandlerMixin:
    """Convert unexpected service errors into safe HTTP responses."""

    def _handle_exception(self, error: Exception, *, action: str) -> HTTPException:
        """Map internal exceptions to sanitized HTTP errors and log them."""
        logger = get_logger(self.__class__.__name__)

        if isinstance(error, HTTPException):
            if error.status_code >= 500:
                log_exception(
                    logger,
                    error,
                    context=f"{self.__class__.__name__}.{action}",
                    source="service",
                    status_code=error.status_code,
                    stacklevel=3,
                )
                return build_logged_http_exception(status_code=error.status_code)
            return error

        log_exception(
            logger,
            error,
            context=f"{self.__class__.__name__}.{action}",
            source="service",
            status_code=500,
            stacklevel=3,
        )
        return build_logged_http_exception()


def register_exception_handlers(app: FastAPI) -> None:
    """Attach shared FastAPI exception handlers to the application."""
    logger = get_logger("api")

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request,
        exc: HTTPException,
    ) -> JSONResponse:
        """Return safe HTTP errors and log untracked server failures."""
        if exc.status_code >= 500 and not getattr(exc, "_arena_logged", False):
            log_exception(
                logger,
                exc,
                context="Unhandled HTTPException",
                source="api",
                status_code=exc.status_code,
                extra={
                    "path": request.url.path,
                    "method": request.method,
                },
            )

        detail = GENERIC_API_ERROR_MESSAGE if exc.status_code >= 500 else exc.detail
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": detail},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """Return validation details while logging request metadata."""
        logger.warning(
            "Request validation failed",
            extra={
                "status_code": 422,
                "context_data": {
                    "source": "api",
                    "context": "RequestValidationError",
                    "path": request.url.path,
                    "method": request.method,
                    "errors": exc.errors(),
                },
            },
        )
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Log any uncaught API exception and return a safe response."""
        log_exception(
            logger,
            exc,
            context="Unhandled API exception",
            source="api",
            status_code=500,
            extra={
                "path": request.url.path,
                "method": request.method,
            },
        )
        return JSONResponse(
            status_code=500,
            content={"detail": GENERIC_API_ERROR_MESSAGE},
        )
