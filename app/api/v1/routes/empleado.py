"""
Endpoints de empleados.
"""
from typing import List

from fastapi import APIRouter, HTTPException, Query

from app.api.dependencias import EmpleadoDependencia, SincronizacionDependencia
from app.core.config import settings
from app.core.exceptions import BioTimeException
from app.schemas.empleado.respuesta_empleado import EmpleadoCreateUpdateDto, EmployeeDto
from app.schemas.respuesta_comun import SuccessResponse
from app.utils.routing import ConfigurableAliasRoute

router = APIRouter(prefix="/empleados", tags=["Employees"], route_class=ConfigurableAliasRoute)


@router.get("", response_model=List[EmployeeDto])
async def obtener_empleados(
    service: EmpleadoDependencia,
    page: int = Query(default=1, ge=1, description="Número de página"),
    page_size: int = Query(default=10, ge=1, le=100, description="Tamaño de página"),
):
    """Obtiene la lista paginada de empleados desde BioTime."""
    try:
        result = await service.obtener_empleados(page=page, page_size=page_size)
        return result.data

    except BioTimeException as e:
        print(f"[Empleado] ERROR - GET /empleados: {e.message} (HTTP {e.status_code})")
        raise HTTPException(status_code=e.status_code, detail={"error": e.message, "status_code": e.status_code})

    except Exception as e:
        print(f"[Empleado] ERROR - GET /empleados: {e}")
        raise HTTPException(status_code=500, detail={"error": "Error interno del servidor", "detail": str(e)})


@router.get("/{empleado_id}", response_model=EmployeeDto)
async def obtener_empleado_por_id(
    service: EmpleadoDependencia,
    empleado_id: int,
):
    """Obtiene un empleado por su ID interno de BioTime."""
    try:
        return await service.obtener_empleado_por_id(empleado_id=empleado_id)

    except BioTimeException as e:
        print(f"[Empleado] ERROR - GET /empleados/{empleado_id}: {e.message} (HTTP {e.status_code})")
        raise HTTPException(status_code=e.status_code, detail={"error": e.message, "status_code": e.status_code})

    except Exception as e:
        print(f"[Empleado] ERROR - GET /empleados/{empleado_id}: {e}")
        raise HTTPException(status_code=500, detail={"error": "Error interno del servidor", "detail": str(e)})


@router.post("", response_model=EmployeeDto, status_code=201)
async def crear_empleado(
    service: EmpleadoDependencia,
    sincronizacion: SincronizacionDependencia,
    datos: EmpleadoCreateUpdateDto,
):
    """Crea un nuevo empleado en BioTime y sincroniza los terminales."""
    try:
        if not datos.area:
            datos.area = [settings.BIOTIME_DEFAULT_AREA_ID]
        empleado = await service.crear_empleado(datos=datos)
        await sincronizacion.sincronizar()
        return empleado

    except BioTimeException as e:
        print(f"[Empleado] ERROR - POST /empleados: {e.message} (HTTP {e.status_code})")
        raise HTTPException(status_code=e.status_code, detail={"error": e.message, "status_code": e.status_code})

    except Exception as e:
        print(f"[Empleado] ERROR - POST /empleados: {e}")
        raise HTTPException(status_code=500, detail={"error": "Error interno del servidor", "detail": str(e)})


@router.put("/{empleado_id}", response_model=EmployeeDto)
async def actualizar_empleado(
    service: EmpleadoDependencia,
    sincronizacion: SincronizacionDependencia,
    empleado_id: int,
    datos: EmpleadoCreateUpdateDto,
):
    """Reemplaza todos los datos de un empleado (PUT) y sincroniza los terminales."""
    try:
        empleado = await service.actualizar_empleado(empleado_id=empleado_id, datos=datos)
        await sincronizacion.sincronizar()
        return empleado

    except BioTimeException as e:
        print(f"[Empleado] ERROR - PUT /empleados/{empleado_id}: {e.message} (HTTP {e.status_code})")
        raise HTTPException(status_code=e.status_code, detail={"error": e.message, "status_code": e.status_code})

    except Exception as e:
        print(f"[Empleado] ERROR - PUT /empleados/{empleado_id}: {e}")
        raise HTTPException(status_code=500, detail={"error": "Error interno del servidor", "detail": str(e)})


@router.delete("", response_model=SuccessResponse)
async def eliminar_empleados(
    service: EmpleadoDependencia,
    sincronizacion: SincronizacionDependencia,
    id: List[int] = Query(..., description="IDs de los empleados a eliminar. Pasar uno o varios: ?ids=1&ids=2&ids=3"),
):
    """Elimina uno o varios empleados por sus IDs y sincroniza los terminales."""
    try:
        eliminados = await service.eliminar_empleados(empleado_ids=id)
        await sincronizacion.sincronizar()
        return SuccessResponse(
            message=f"{eliminados} empleado(s) eliminado(s) correctamente.",
            data={"ids_eliminados": id, "total": eliminados},
        )

    except BioTimeException as e:
        print(f"[Empleado] ERROR - DELETE /empleados IDs={id}: {e.message} (HTTP {e.status_code})")
        raise HTTPException(status_code=e.status_code, detail={"error": e.message, "status_code": e.status_code})

    except Exception as e:
        print(f"[Empleado] ERROR - DELETE /empleados IDs={id}: {e}")
        raise HTTPException(status_code=500, detail={"error": "Error interno del servidor", "detail": str(e)})
