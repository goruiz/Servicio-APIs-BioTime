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