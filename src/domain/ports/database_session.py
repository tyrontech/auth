"""
Protocolo para abstracción de sesión de base de datos.
Permite que el dominio y la aplicación no dependan de implementaciones específicas (SQLAlchemy, etc).

Este protocolo expone solo las operaciones esenciales necesarias para los repositorios.
Las implementaciones concretas (SQLAlchemy, etc) viven en la capa de infraestructura.
"""
from typing import Protocol, Any, Awaitable
from typing_extensions import runtime_checkable


@runtime_checkable
class IDatabaseSession(Protocol):
    """
    Protocolo para sesión de base de datos.
    
    Las implementaciones deben proveer métodos para:
    - Ejecutar queries
    - Agregar/modificar/eliminar entidades
    - Hacer commit de transacciones
    - Refrescar entidades desde la BD
    """
    
    async def execute(self, statement: Any) -> Any:
        """
        Ejecuta una statement (query) y retorna el resultado.
        
        Args:
            statement: Statement a ejecutar (query, update, delete, etc)
            
        Returns:
            Resultado de la ejecución (Result, CursorResult, etc)
        """
        ...
    
    def add(self, instance: Any) -> None:
        """
        Agrega una instancia a la sesión para ser persistida.
        
        Args:
            instance: Instancia a agregar
        """
        ...
    
    async def commit(self) -> None:
        """
        Hace commit de la transacción actual.
        """
        ...
    
    async def refresh(self, instance: Any) -> None:
        """
        Refresca una instancia desde la base de datos.
        
        Args:
            instance: Instancia a refrescar
        """
        ...
    
    def delete(self, instance: Any) -> None:
        """
        Marca una instancia para ser eliminada.
        Nota: Este método es síncrono (como en SQLAlchemy).
        
        Args:
            instance: Instancia a eliminar
        """
        ...
    
    async def close(self) -> None:
        """
        Cierra la sesión y libera recursos.
        """
        ...
