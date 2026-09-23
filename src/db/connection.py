"""
Async database connection management.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.config import settings

_engine = None
_AsyncSessionLocal = None

def get_engine():
    global _engine
    if _engine is None:
        try:
            _engine = create_async_engine(
                settings.database_url,
                echo=settings.log_level == "DEBUG",
                pool_size=5,
                max_overflow=10
            )
        except Exception:
            # Fallback for lightweight / test environments without asyncpg driver
            try:
                _engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
            except Exception:
                _engine = None
    return _engine

def get_session_factory():
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        engine = get_engine()
        if engine is not None:
            _AsyncSessionLocal = async_sessionmaker(
                engine, 
                expire_on_commit=False,
                class_=AsyncSession
            )
    return _AsyncSessionLocal

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to provide a database session.
    """
    session_factory = get_session_factory()
    if session_factory is None:
        raise RuntimeError("Database session factory is not available in current environment")
    async with session_factory() as session:
        yield session
