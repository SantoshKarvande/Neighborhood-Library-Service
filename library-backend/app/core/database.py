"""
Async SQLAlchemy engine and session factory.
DATABASE_URL is read from the environment variable of the same name.
"""

import os

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://library_user:library_pass@localhost:5432/library_db",
)

engine = create_async_engine(
    DATABASE_URL,
    echo=bool(os.getenv("SQL_ECHO", "")),   # set SQL_ECHO=1 to log queries
    pool_size=10,
    max_overflow=20,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:           # type: ignore[return]
    """FastAPI dependency – yields a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


