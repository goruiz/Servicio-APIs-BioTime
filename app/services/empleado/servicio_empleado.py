"""
Servicio de empleados.
Lógica de negocio para interactuar con el recurso de empleados de BioTime.
"""
from app.clients.biotime_client import BioTimeClient
from app.core.logging import get_logger
from app.interfaces.empleado.interface_empleado import IEmpleado
from app.schemas.biotime.common import PaginatedResponse
from app.schemas.empleado.respuesta_empleado import EmployeeDto

logger = get_logger(__name__)


class ServicioEmpleado(IEmpleado):
    """Implementación del servicio de empleados."""

    def __init__(self, client: BioTimeClient):
        self._client = client

    async def obtener_empleados(
        self, page: int = 1, page_size: int = 10
    ) -> PaginatedResponse[EmployeeDto]:
        """Obtiene la lista paginada de empleados desde BioTime."""
        logger.info("Obteniendo empleados", page=page, page_size=page_size)
        params = {"page": page, "page_size": page_size}
        response_data = await self._client.get("personnel/api/employees/", params=params)
        employees = [EmployeeDto(**emp) for emp in response_data.get("data", [])]
        result = PaginatedResponse[EmployeeDto](
            count=response_data.get("count", 0),
            next=response_data.get("next"),
            previous=response_data.get("previous"),
            data=employees,
        )
        logger.info(
            "Empleados obtenidos exitosamente",
            total=result.count,
            page=page,
            returned=len(employees),
        )
        return result
