"""
Interfaz del servicio de áreas de BioTime.
"""
from abc import ABC, abstractmethod

from app.schemas.biotime.common import PaginatedResponse
from app.schemas.areas.respuesta_areas import AreaDto


class IAreas(ABC):

    @abstractmethod
    async def obtener_areas(
        self, page: int = 1, page_size: int = 10
    ) -> PaginatedResponse[AreaDto]:
        """Obtiene la lista paginada de áreas registradas en BioTime."""
        pass

    @abstractmethod
    async def obtener_area_por_id(self, area_id: int) -> AreaDto:
        """Obtiene un área por su ID interno de BioTime."""
        pass
