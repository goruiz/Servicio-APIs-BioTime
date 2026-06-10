"""
Interfaz del servicio de BioTime.
Define el contrato que debe cumplir cualquier implementación del servicio.
"""
from abc import ABC, abstractmethod
from typing import Optional

from app.schemas.biotime.common import PaginatedResponse
from app.schemas.marcaciones.respuesta_marcaciones import MarcacionesDto


class IMarcaciones(ABC):
    """Interfaz para el servicio de BioTime."""

    @abstractmethod
    async def obtener_marcaciones(
        self, page: int = 1, page_size: int = 10
    ) -> PaginatedResponse[MarcacionesDto]:
        """
        Obtiene la lista paginada de marcaciones desde BioTime.

        Args:
            page: Número de página (inicia en 1)
            page_size: Cantidad de registros por página

        Returns:
            PaginatedResponse con la lista de marcaciones

        Raises:
            BioTimeAuthenticationError: Si hay error de autenticación
            BioTimeConnectionError: Si hay error de conexión
        """
        pass

    @abstractmethod
    async def obtener_marcaciones_por_empleado(
        self, codigo_empleado: str, fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None, page: int = 1, page_size: int = 10
    ) -> PaginatedResponse[MarcacionesDto]:
        """
        Obtiene la lista paginada de marcaciones desde BioTime.

        Args:
            page: Número de página (inicia en 1)
            page_size: Cantidad de registros por página

        Returns:
            PaginatedResponse con la lista de marcaciones

        Raises:
            BioTimeAuthenticationError: Si hay error de autenticación
            BioTimeConnectionError: Si hay error de conexión
        """
        pass

    @abstractmethod
    async def obtener_marcaciones_por_terminal(
        self, terminal_sn: str, fecha_inicio: str, page_size: int = 100
    ) -> list[MarcacionesDto]:
        """Obtiene todas las marcaciones de un terminal desde una fecha, paginando internamente."""
        pass

    @abstractmethod
    async def obtener_marcaciones_por_serial(
        self,
        terminal_sn: str,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> PaginatedResponse[MarcacionesDto]:
        """Obtiene la lista paginada de marcaciones de un terminal por su número de serie."""
        pass

    @abstractmethod
    async def obtener_marcaciones_por_ip(
        self,
        ip_terminal: str,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> PaginatedResponse[MarcacionesDto]:
        """Obtiene marcaciones de un terminal buscando por su dirección IP."""
        pass

    @abstractmethod
    async def eliminar_marcaciones_por_id(
        self, id_marcacion: str
    ) -> None:
        """
        Elimina las marcaciones de un empleado desde BioTime.

        Args:
            page: Número de página (inicia en 1)
            page_size: Cantidad de registros por página

        Returns:
            PaginatedResponse con la lista de marcaciones

        Raises:
            BioTimeAuthenticationError: Si hay error de autenticación
            BioTimeConnectionError: Si hay error de conexión
        """
        pass

    @abstractmethod
    async def eliminar_marcaciones(
        self,
        codigo_empleado: Optional[str] = None,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
    ) -> int:
        """
        Elimina marcaciones filtrando por empleado y/o rango de fechas.

        Obtiene todos los IDs que coincidan con los filtros (paginando internamente)
        y los elimina uno a uno.

        Args:
            codigo_empleado: Código del empleado en BioTime (emp_code). Opcional.
            fecha_inicio: Límite inferior del rango (ej: '2024-01-01 00:00:00'). Opcional.
            fecha_fin: Límite superior del rango (ej: '2024-01-31 23:59:59'). Opcional.

        Returns:
            Número de marcaciones eliminadas.

        Raises:
            BioTimeAuthenticationError: Si hay error de autenticación
            BioTimeConnectionError: Si hay error de conexión
        """
        pass