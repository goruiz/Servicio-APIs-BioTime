"""
Servicio de empleados.
Lógica de negocio para interactuar con el recurso de empleados de BioTime.
"""
from app.clients.biotime_client import BioTimeClient
from app.core.logging import get_logger
from app.interfaces.empleado.interface_empleado import IEmpleado
from app.schemas.biotime.common import PaginatedResponse
from app.schemas.empleado.respuesta_empleado import EmpleadoCreateUpdateDto, EmployeeDto

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

    async def obtener_empleado_por_id(self, empleado_id: int) -> EmployeeDto:
        """Obtiene un empleado por su ID interno de BioTime."""
        logger.info("Obteniendo empleado por ID", empleado_id=empleado_id)
        response_data = await self._client.get(f"personnel/api/employees/{empleado_id}/")
        empleado = EmployeeDto(**response_data)
        logger.info("Empleado obtenido exitosamente", empleado_id=empleado_id)
        return empleado

    async def crear_empleado(self, datos: EmpleadoCreateUpdateDto) -> EmployeeDto:
        """Crea un nuevo empleado en BioTime."""
        logger.info("Creando empleado", emp_code=datos.emp_code)
        response_data = await self._client.post(
            "personnel/api/employees/", json=datos.model_dump()
        )
        empleado = EmployeeDto(**response_data)
        logger.info("Empleado creado exitosamente", empleado_id=empleado.id, emp_code=empleado.emp_code)
        return empleado

    async def actualizar_empleado(self, empleado_id: int, datos: EmpleadoCreateUpdateDto) -> EmployeeDto:
        """Reemplaza todos los datos de un empleado (PUT)."""
        logger.info("Actualizando empleado", empleado_id=empleado_id, emp_code=datos.emp_code)
        response_data = await self._client.put(
            f"personnel/api/employees/{empleado_id}/", json=datos.model_dump()
        )
        empleado = EmployeeDto(**response_data)
        logger.info("Empleado actualizado exitosamente", empleado_id=empleado_id)
        return empleado

    async def eliminar_empleado(self, empleado_id: int) -> None:
        """Elimina un empleado por su ID interno de BioTime."""
        logger.info("Eliminando empleado", empleado_id=empleado_id)
        await self._client.delete(f"personnel/api/employees/{empleado_id}/")
        logger.info("Empleado eliminado exitosamente", empleado_id=empleado_id)
