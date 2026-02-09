"""
Fábrica del motor y sesiones asíncronas para SQLAlchemy.
Sin dependencias de config: recibe URL y opciones por parámetro.
La composición con config se hace en el composition root (deps).
"""
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_async_engine_and_session_factory(
    url: str,
    *,
    echo: bool = False,
    pool_size: int = 20,
    max_overflow: int = 0,
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """
    Crea motor asíncrono y fábrica de sesiones. Infra no conoce config.
    """
    engine = create_async_engine(
        url,
        echo=echo,
        future=True,
        pool_size=pool_size,
        max_overflow=max_overflow,
    )
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=True,
    )
    return engine, session_factory


