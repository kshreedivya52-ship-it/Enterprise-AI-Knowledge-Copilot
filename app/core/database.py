import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

# Database connection string: postgresql+asyncpg://<user>:<password>@<host>:<port>/<dbname>
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://user:password@localhost:5433/copilot_db"
)

# 1. Engine: Manages connection pool to PostgreSQL using asyncpg driver
engine = create_async_engine(
    DATABASE_URL,
    echo=True,              # Set to True to print executed SQL statements in console (great for debugging)
    future=True
)

# 2. Session Maker: Factory for creating async database sessions
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Prevents SQLAlchemy from expiring objects after commit in async mode
    autoflush=False
)

# 3. Base Class: Parent model class that all ORM entities will inherit from
class Base(DeclarativeBase):
    pass

# 4. FastAPI Dependency: Yields a session per request and guarantees cleanup
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency generator for FastAPI endpoints.
    Provides an isolated database session per request and automatically closes it when done.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
