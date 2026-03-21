"""
Database engine and session management.
Uses SQLAlchemy 2.0 async.
Supports SQLite (dev) and PostgreSQL (production).
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from src.config import get_settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


settings = get_settings()

# SQLite doesn't support pool_size/max_overflow
_is_sqlite = settings.db.url.startswith("sqlite")

engine_kwargs = {"echo": settings.db.echo}
if not _is_sqlite:
    engine_kwargs["pool_size"] = settings.db.pool_size
    engine_kwargs["max_overflow"] = settings.db.max_overflow

engine = create_async_engine(settings.db.url, **engine_kwargs)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """FastAPI dependency: yields a database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create all tables. Use Alembic for production migrations."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Cleanup on shutdown."""
    await engine.dispose()
