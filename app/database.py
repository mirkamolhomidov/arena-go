"""Configure the shared async SQLModel engine and session factory."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app import models  # noqa: F401
from app.core.config import settings


DATABASE_URL = settings.DATABASE_URL_ASYNC
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=settings.SQL_ECHO,
    pool_pre_ping=True,
)
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def create_db_and_tables() -> None:
    """Create database tables for local development bootstrap."""
    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)


async def close_db_engine() -> None:
    """Dispose the shared async engine during application shutdown."""
    await engine.dispose()


async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield an async database session for request handlers."""
    async with async_session_factory() as session:
        yield session
