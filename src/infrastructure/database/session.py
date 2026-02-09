"""
Fábrica del motor y sesiones asíncronas para SQLAlchemy.
Sin dependencias de config: recibe URL y opciones por parámetro.
La composición con config se hace en el composition root (bootstrap).
"""
from typing import AsyncGenerator

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


def create_get_db(
    session_factory: async_sessionmaker[AsyncSession],
):
    """
    Devuelve la función get_db (generador de sesión por request).
    La lógica de ciclo de vida vive en infra; el composition root la usa.
    """

    async def get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
            finally:
                await session.close()

    return get_db


def create_db_provider(
    url: str,
    *,
    echo: bool = False,
    pool_size: int = 20,
    max_overflow: int = 0,
):
    """
    Crea el proveedor de sesión (get_db) a partir de URL y opciones.
    Usado por el composition root (bootstrap); infra no lee config.
    """
    engine, session_factory = create_async_engine_and_session_factory(
        url, echo=echo, pool_size=pool_size, max_overflow=max_overflow
    )
    return create_get_db(session_factory)
