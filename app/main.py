"""Create and configure the FastAPI application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.error_handling import register_exception_handlers
from app.core.logger import get_logger, setup_logging
from app.database import close_db_engine, create_db_and_tables
from app.routers.routers import Routes


setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup tasks before serving requests."""
    logger.info("Starting FastAPI application")
    await create_db_and_tables()
    yield
    await close_db_engine()
    logger.info("Stopping FastAPI application")

app = FastAPI(
    title="Stadium bot API",
    version="1.0.0",
    lifespan=lifespan
)

Routes('/api', app)
register_exception_handlers(app)

@app.get("/")
async def root():
    """Return a lightweight health check response."""
    return {"message": "OK"}
