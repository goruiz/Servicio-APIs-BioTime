"""
Servicio de empleados.
Lógica de negocio para interactuar con el recurso de empleados de BioTime.
"""
from typing import Optional

from app.clients.biotime_client import BioTimeClient
from app.core.config import settings
from app.interfaces.empleado.interface_empleado import IEmpleado
from app.schemas.biotime.common import PaginatedResponse
from app.schemas.empleado.respuesta_empleado import EmpleadoCreateUpdateDto, EmployeeDto


class ServicioEmpleado(IEmpleado):
    """Implementación del servicio de empleados."""

    def __init__(self, client: BioTimeClient):
        self._client = client

    async def obtener_empleados(self, page: int = 1, page_size: int = 10) -> PaginatedResponse[EmployeeDto]:
        params = {"page": page, "page_size": page_size}
        response_data = await self._client.get("personnel/api/employees/", params=params)
        employees = [EmployeeDto(**emp) for emp in response_data.get("data", [])]
        result = PaginatedResponse[EmployeeDto](
            count=response_data.get("count", 0),
            next=response_data.get("next"),
            previous=response_data.get("previous"),
            data=employees,
        )
        print(f"[Empleado] Obtenidos {len(employees)}/{result.count} — página {page}")
        return result

    async def obtener_empleado_por_id(self, empleado_id: int) -> EmployeeDto:
        response_data = await self._client.get(f"personnel/api/employees/{empleado_id}/")
        empleado = EmployeeDto(**response_data)
        print(f"[Empleado] Obtenido — ID={empleado_id} emp_code={empleado.emp_code}")
        return empleado

    async def buscar_por_emp_code(self, emp_code: str) -> Optional[EmployeeDto]:
        response_data = await self._client.get("personnel/api/employees/", params={"emp_code": emp_code})
        empleados = response_data.get("data", [])
        if not empleados:
            return None
        return EmployeeDto(**empleados[0])

    async def crear_empleado(self, datos: EmpleadoCreateUpdateDto) -> EmployeeDto:
        if not datos.area:
            datos.area = [settings.BIOTIME_DEFAULT_AREA_ID]
        response_data = await self._client.post("personnel/api/employees/", json=datos.model_dump())
        # BioTime a veces no incluye id en la respuesta del POST; lo buscamos por emp_code
        if response_data.get("id"):
            empleado = EmployeeDto(**response_data)
        else:
            empleado = await self.buscar_por_emp_code(datos.emp_code)
            if not empleado:
                raise ValueError(f"Empleado creado pero no encontrado en BioTime: emp_code={datos.emp_code}")
        return empleado

    async def actualizar_empleado(self, empleado_id: int, datos: EmpleadoCreateUpdateDto) -> EmployeeDto:
        response_data = await self._client.put(
            f"personnel/api/employees/{empleado_id}/", json=datos.model_dump()
        )
        # BioTime a veces no incluye id en la respuesta del PUT; lo obtenemos por ID directo
        if response_data.get("id"):
            empleado = EmployeeDto(**response_data)
        else:
            empleado = await self.obtener_empleado_por_id(empleado_id)
        print(f"[Empleado] Actualizado — ID={empleado_id}")
        return empleado

    async def eliminar_empleados(self, empleado_ids: list[int]) -> int:
        for empleado_id in empleado_ids:
            await self._client.delete(f"personnel/api/employees/{empleado_id}/")
        print(f"[Empleado] Eliminados {len(empleado_ids)} — IDs={empleado_ids}")
        return len(empleado_ids)
