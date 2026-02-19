"""
Interfaz del servicio de BioTime.
Define el contrato que debe cumplir cualquier implementación del servicio.
"""
from abc import ABC, abstractmethod

from app.schemas.biotime.common import PaginatedResponse
from app.schemas.empleado.respuesta_empleado import EmpleadoCreateUpdateDto, EmployeeDto


class IEmpleado(ABC):
    """Interfaz para el servicio de BioTime."""

    @abstractmethod
    async def obtener_empleados(
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

    @abstractmethod
    async def obtener_empleado_por_id(self, empleado_id: int) -> EmployeeDto:
        """Obtiene un empleado por su ID interno de BioTime."""
        pass

    @abstractmethod
    async def crear_empleado(self, datos: EmpleadoCreateUpdateDto) -> EmployeeDto:
        """Crea un nuevo empleado en BioTime. Devuelve el empleado creado."""
        pass

    @abstractmethod
    async def actualizar_empleado(self, empleado_id: int, datos: EmpleadoCreateUpdateDto) -> EmployeeDto:
        """Reemplaza todos los datos de un empleado (PUT). Devuelve el empleado actualizado."""
        pass

    @abstractmethod
    async def eliminar_empleado(self, empleado_id: int) -> None:
        """Elimina un empleado por su ID interno de BioTime."""
        pass
