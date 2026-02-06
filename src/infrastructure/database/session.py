from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config.settings import get_database_url

DATABASE_URL = get_database_url()

# Create Async Engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True, # Set to False in production
    future=True
)

# Create Async Session Factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncSession:
    """
    Dependency generator for FastAPI to yield Database Sessions.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
