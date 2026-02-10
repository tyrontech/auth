"""
Fábrica del motor y sesiones asíncronas para SQLAlchemy.
Sin dependencias de config: recibe URL y opciones por parámetro.
La composición con config se hace en el composition root (bootstrap).
"""
from typing import AsyncGenerator, Callable

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from infrastructure.database.session_adapter import SQLAlchemySessionAdapter
from domain.ports.database_session import IDatabaseSession


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
    
    Retorna IDatabaseSession (wrappeado con SQLAlchemySessionAdapter)
    para que el dominio no conozca SQLAlchemy.
    """

    async def get_db() -> AsyncGenerator[IDatabaseSession, None]:
        async with session_factory() as raw_session:
            try:
                # Wrappear AsyncSession con el adapter que implementa IDatabaseSession
                yield SQLAlchemySessionAdapter(raw_session)
            finally:
                await raw_session.close()

    return get_db


def create_db_provider(
    url: str,
    *,
    echo: bool = False,
    pool_size: int = 20,
    max_overflow: int = 0,
) -> tuple[AsyncEngine, Callable[[], AsyncGenerator[IDatabaseSession, None]]]:
    """
    Crea el proveedor de sesión (get_db) y retorna el engine para gestión de ciclo de vida.
    Usado por el composition root (bootstrap); infra no lee config.
    
    Returns:
        Tuple[AsyncEngine, callable]: (engine, get_db_function)
        El engine debe ser cerrado con engine.dispose() durante shutdown.
    """
    engine, session_factory = create_async_engine_and_session_factory(
        url, echo=echo, pool_size=pool_size, max_overflow=max_overflow
    )
    return engine, create_get_db(session_factory)
