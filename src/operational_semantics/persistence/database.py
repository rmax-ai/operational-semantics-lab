"""SQLite database engine setup with WAL mode and connection management."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# Default to in-memory for tests, file-based for demo/api
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/operational_semantics.db")
# In-memory override for tests
TEST_DATABASE_URL = "sqlite+aiosqlite://"


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all table models."""

    pass


_engine = None
_session_factory = None


def get_engine(database_url: str | None = None) -> "AsyncEngine":
    """Get or create the SQLAlchemy async engine."""
    global _engine
    if _engine is None:
        url = database_url or DATABASE_URL
        _engine = create_async_engine(url, echo=False)

        @event.listens_for(_engine.sync_engine, "connect")
        def _apply_sqlite_pragmas(dbapi_connection: object, _: object) -> None:
            from sqlalchemy import text as sa_text

            with dbapi_connection as conn:  # type: ignore
                conn.execute(sa_text("PRAGMA journal_mode=WAL;"))
                conn.execute(sa_text("PRAGMA synchronous=NORMAL;"))
                conn.execute(sa_text("PRAGMA foreign_keys=ON;"))
                conn.execute(sa_text("PRAGMA busy_timeout=5000;"))
                conn.execute(sa_text("PRAGMA cache_size=-64000;"))

    return _engine


def get_session_factory(engine=None) -> async_sessionmaker[AsyncSession]:
    """Get or create the async session factory."""
    global _session_factory
    if _session_factory is None or engine is not None:
        eng = engine or get_engine()
        _session_factory = async_sessionmaker(eng, expire_on_commit=False)
    return _session_factory


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """Get an async session for database operations."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db(database_url: str | None = None) -> None:
    """Initialize the database schema."""
    engine = get_engine(database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def teardown_db() -> None:
    """Dispose of the database engine."""
    global _engine, _session_factory
    if _engine:
        await _engine.dispose()
        _engine = None
        _session_factory = None
