"""
Adapter que implementa IDatabaseSession usando SQLAlchemy AsyncSession.
Este adapter permite que el dominio use el protocolo sin conocer SQLAlchemy.
"""
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from domain.ports.database_session import IDatabaseSession


class SQLAlchemySessionAdapter:
    """
    Adapter que wrappea AsyncSession de SQLAlchemy para implementar IDatabaseSession.
    
    Este adapter permite que el dominio y la aplicación usen el protocolo IDatabaseSession
    sin conocer detalles de implementación de SQLAlchemy.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Args:
            session: AsyncSession de SQLAlchemy a wrappear
        """
        self._session = session
    
    async def execute(self, statement: Any) -> Any:
        """Ejecuta una statement de SQLAlchemy."""
        return await self._session.execute(statement)
    
    def add(self, instance: Any) -> None:
        """Agrega una instancia a la sesión."""
        self._session.add(instance)
    
    async def commit(self) -> None:
        """Hace commit de la transacción."""
        await self._session.commit()
    
    async def refresh(self, instance: Any) -> None:
        """Refresca una instancia desde la BD."""
        await self._session.refresh(instance)
    
    def delete(self, instance: Any) -> None:
        """Marca una instancia para ser eliminada."""
        self._session.delete(instance)
    
    async def close(self) -> None:
        """Cierra la sesión."""
        await self._session.close()
    
    @property
    def raw_session(self) -> AsyncSession:
        """
        Acceso a la sesión raw de SQLAlchemy (solo para casos especiales en infraestructura).
        No debería usarse fuera de la capa de infraestructura.
        """
        return self._session


# Type check: asegurar que el adapter implementa el protocolo
def _type_check() -> None:
    """Type check helper - no se ejecuta, solo para verificación de tipos."""
    adapter: IDatabaseSession = SQLAlchemySessionAdapter(
        session=None  # type: ignore
    )
