"""
Endpoints de empleados.
"""
from typing import List

from fastapi import APIRouter, HTTPException, Query

from app.api.dependencias import EmpleadoDependencia, SincronizacionDependencia
from app.core.exceptions import BioTimeException
from app.core.logging import get_logger
from app.schemas.empleado.respuesta_empleado import EmpleadoCreateUpdateDto, EmployeeDto
from app.utils.routing import ConfigurableAliasRoute

logger = get_logger(__name__)
router = APIRouter(prefix="/empleados", tags=["Employees"], route_class=ConfigurableAliasRoute)


@router.get("", response_model=List[EmployeeDto])
async def obtener_empleados(
    service: EmpleadoDependencia,
    page: int = Query(default=1, ge=1, description="Número de página"),
    page_size: int = Query(default=10, ge=1, le=100, description="Tamaño de página"),
):
    """Obtiene la lista paginada de empleados desde BioTime."""
    try:
        logger.info("GET /employees", page=page, page_size=page_size)
        result = await service.obtener_empleados(page=page, page_size=page_size)
        return result.data

    except BioTimeException as e:
        logger.error("Error de BioTime al obtener empleados", error=e.message, status_code=e.status_code)
        raise HTTPException(status_code=e.status_code, detail={"error": e.message, "status_code": e.status_code})

    except Exception as e:
        logger.error("Error inesperado al obtener empleados", error=str(e))
        raise HTTPException(status_code=500, detail={"error": "Error interno del servidor", "detail": str(e)})


@router.get("/{empleado_id}", response_model=EmployeeDto)
async def obtener_empleado_por_id(
    service: EmpleadoDependencia,
    empleado_id: int,
):
    """Obtiene un empleado por su ID interno de BioTime."""
    try:
        logger.info("GET /employees/{id}", empleado_id=empleado_id)
        return await service.obtener_empleado_por_id(empleado_id=empleado_id)

    except BioTimeException as e:
        logger.error("Error de BioTime al obtener empleado", empleado_id=empleado_id, error=e.message, status_code=e.status_code)
        raise HTTPException(status_code=e.status_code, detail={"error": e.message, "status_code": e.status_code})

    except Exception as e:
        logger.error("Error inesperado al obtener empleado", empleado_id=empleado_id, error=str(e))
        raise HTTPException(status_code=500, detail={"error": "Error interno del servidor", "detail": str(e)})


@router.post("", response_model=EmployeeDto, status_code=201)
async def crear_empleado(
    service: EmpleadoDependencia,
    sincronizacion: SincronizacionDependencia,
    datos: EmpleadoCreateUpdateDto,
):
    """Crea un nuevo empleado en BioTime y sincroniza los terminales."""
    try:
        logger.info("POST /employees", emp_code=datos.emp_code)
        empleado = await service.crear_empleado(datos=datos)
        await sincronizacion.sincronizar()
        return empleado

    except BioTimeException as e:
        logger.error("Error de BioTime al crear empleado", error=e.message, status_code=e.status_code)
        raise HTTPException(status_code=e.status_code, detail={"error": e.message, "status_code": e.status_code})

    except Exception as e:
        logger.error("Error inesperado al crear empleado", error=str(e))
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
        logger.info("PUT /employees/{id}", empleado_id=empleado_id, emp_code=datos.emp_code)
        empleado = await service.actualizar_empleado(empleado_id=empleado_id, datos=datos)
        await sincronizacion.sincronizar()
        return empleado

    except BioTimeException as e:
        logger.error("Error de BioTime al actualizar empleado", empleado_id=empleado_id, error=e.message, status_code=e.status_code)
        raise HTTPException(status_code=e.status_code, detail={"error": e.message, "status_code": e.status_code})

    except Exception as e:
        logger.error("Error inesperado al actualizar empleado", empleado_id=empleado_id, error=str(e))
        raise HTTPException(status_code=500, detail={"error": "Error interno del servidor", "detail": str(e)})


@router.delete("", status_code=204)
async def eliminar_empleados(
    service: EmpleadoDependencia,
    sincronizacion: SincronizacionDependencia,
    id: List[int] = Query(..., description="IDs de los empleados a eliminar. Pasar uno o varios: ?ids=1&ids=2&ids=3"),
):
    """Elimina uno o varios empleados por sus IDs y sincroniza los terminales."""
    try:
        logger.info("DELETE /empleados", ids=id, total=len(id))
        await service.eliminar_empleados(empleado_ids=id)
        await sincronizacion.sincronizar()

    except BioTimeException as e:
        logger.error("Error de BioTime al eliminar empleados", ids=id, error=e.message, status_code=e.status_code)
        raise HTTPException(status_code=e.status_code, detail={"error": e.message, "status_code": e.status_code})

    except Exception as e:
        logger.error("Error inesperado al eliminar empleados", ids=id, error=str(e))
        raise HTTPException(status_code=500, detail={"error": "Error interno del servidor", "detail": str(e)})
