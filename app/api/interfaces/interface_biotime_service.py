"""
Interfaz del servicio de BioTime.
Define el contrato que debe cumplir cualquier implementación del servicio.
"""
from abc import ABC, abstractmethod

from app.schemas.biotime.common import PaginatedResponse
from app.schemas.empleado.respuesta_empleado import EmployeeDto


class IBioTimeService(ABC):
    """Interfaz para el servicio de BioTime."""

    @abstractmethod
    async def get_employees(
        self, page: int = 1, page_size: int = 10
    ) -> PaginatedResponse[EmployeeDto]:
        """
        Obtiene la lista paginada de empleados desde BioTime.

        Args:
            page: Número de página (inicia en 1)
            page_size: Cantidad de registros por página

        Returns:
            PaginatedResponse con la lista de empleados

        Raises:
            BioTimeAuthenticationError: Si hay error de autenticación
            BioTimeConnectionError: Si hay error de conexión
        """
        pass
