"""
Interfaz del servicio de huellas dactilares.
"""
from abc import ABC, abstractmethod

from app.schemas.biotime.common import PaginatedResponse
from app.schemas.huellas.respuesta_huellas import HuellaDto


class IHuellas(ABC):

    @abstractmethod
    async def obtener_huellas(
        self, page: int = 1, page_size: int = 10
    ) -> PaginatedResponse[HuellaDto]:
        """Obtiene la lista paginada de todas las huellas registradas en BioTime."""
        pass

    @abstractmethod
    async def obtener_huellas_por_empleado(
        self, empleado_id: int, page: int = 1, page_size: int = 10
    ) -> PaginatedResponse[HuellaDto]:
        """Obtiene las huellas registradas de un empleado específico por su employee_id (PK en iclock_biodata)."""
        pass

    @abstractmethod
    async def obtener_huellas_por_terminal(
        self, sn: str, page: int = 1, page_size: int = 10
    ) -> PaginatedResponse[HuellaDto]:
        """Obtiene las huellas registradas en un terminal específico por su número de serie (SN)."""
        pass
