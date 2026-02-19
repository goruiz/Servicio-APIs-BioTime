"""
Endpoints de empleados.
"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.api.dependencias import MarcacionesDependencia, SincronizacionDependencia
from app.core.exceptions import BioTimeException
from app.core.logging import get_logger
from app.schemas.marcaciones.respuesta_marcaciones import MarcacionesDto
from app.utils.routing import ConfigurableAliasRoute

logger = get_logger(__name__)
router = APIRouter(prefix="/marcaciones", tags=["Marcaciones"], route_class=ConfigurableAliasRoute)


@router.get("", response_model=List[MarcacionesDto])
async def obtener_marcaciones(service: MarcacionesDependencia,  page: int = Query(default=1, ge=1, description="Número de página"),  page_size: int = Query(default=10, ge=1, le=100, description="Tamaño de página")):
    """
    Obtiene la lista paginada de marcaciones desde BioTime.

    Args:
        service: Servicio de BioTime inyectado
        page: Número de página (mínimo 1)
        page_size: Cantidad de registros por página (1-100)

    Returns:
        Lista de marcaciones

    Raises:
        HTTPException: Si hay error al obtener los marcaciones
    """
    try:
        logger.info("GET /marcaciones", page=page, page_size=page_size)
        result = await service.obtener_marcaciones(page=page, page_size=page_size)
        return result.data

    except BioTimeException as e:
        logger.error(
            "Error de BioTime al obtener marcaciones",
            error=e.message,
            status_code=e.status_code,
        )
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": e.message, "status_code": e.status_code},
        )

    except Exception as e:
        logger.error("Error inesperado al obtener marcaciones", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": "Error interno del servidor", "detail": str(e)},
        )

@router.get("/por-empleado", response_model=List[MarcacionesDto])
async def obtener_marcaciones_por_empleado(
    service: MarcacionesDependencia,
    codigo_empleado: str = Query(..., description="Código de empleado"),
    fecha_inicio: Optional[str] = Query(default=None, description="Fecha de inicio (ej: 2024-01-01 00:00:00)"),
    fecha_fin: Optional[str] = Query(default=None, description="Fecha de fin (ej: 2024-01-31 23:59:59)"),
    page: int = Query(default=1, ge=1, description="Número de página"),
    page_size: int = Query(default=10, ge=1, le=100, description="Tamaño de página"),
):
    """
    Obtiene la lista paginada de marcaciones desde BioTime por empleado.

    Args:
        service: Servicio de BioTime inyectado
        codigo_empleado: Código del empleado
        fecha_inicio: Fecha de inicio del rango (opcional)
        fecha_fin: Fecha de fin del rango (opcional)
        page: Número de página (mínimo 1)
        page_size: Cantidad de registros por página (1-100)

    Returns:
        Lista de marcaciones por empleado

    Raises:
        HTTPException: Si hay error al obtener los marcaciones por empleado
    """
    try:
        logger.info("GET /marcaciones/por-empleado", codigo_empleado=codigo_empleado, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, page=page, page_size=page_size)
        result = await service.obtener_marcaciones_por_empleado(codigo_empleado=codigo_empleado, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, page=page, page_size=page_size)
        return result.data

    except BioTimeException as e:
        logger.error(
            "Error de BioTime al obtener marcaciones por código de empleado",
            error=e.message,
            status_code=e.status_code,
        )
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": e.message, "status_code": e.status_code},
        )

    except Exception as e:
        logger.error("Error inesperado al obtener marcaciones por código de empleado", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": "Error interno del servidor", "detail": str(e)},
        )



@router.delete("/por-filtro")
async def eliminar_marcaciones(
    service: MarcacionesDependencia,
    sincronizacion: SincronizacionDependencia,
    codigo_empleado: Optional[str] = Query(default=None, description="Código de empleado (emp_code en BioTime)"),
    fecha_inicio: Optional[str] = Query(default=None, description="Fecha de inicio del rango (ej: 2024-01-01 00:00:00)"),
    fecha_fin: Optional[str] = Query(default=None, description="Fecha de fin del rango (ej: 2024-01-31 23:59:59)"),
):
    """
    Elimina marcaciones filtrando por empleado y/o rango de fechas.

    Se debe proporcionar al menos un filtro:
    - Solo rango de fechas: elimina todas las marcaciones dentro del rango.
    - Solo codigo_empleado: elimina todas las marcaciones del empleado.
    - Ambos: elimina las marcaciones del empleado dentro del rango de fechas.
    """
    if not any([codigo_empleado, fecha_inicio, fecha_fin]):
        raise HTTPException(
            status_code=400,
            detail={"error": "Debe proporcionar al menos un filtro: codigo_empleado, fecha_inicio o fecha_fin"},
        )

    try:
        logger.info(
            "DELETE /marcaciones/por-filtro",
            codigo_empleado=codigo_empleado,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )
        eliminadas = await service.eliminar_marcaciones(
            codigo_empleado=codigo_empleado,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )
        await sincronizacion.sincronizar()
        return {"message": "Marcaciones eliminadas exitosamente", "eliminadas": eliminadas}

    except BioTimeException as e:
        logger.error(
            "Error de BioTime al eliminar marcaciones por filtro",
            error=e.message,
            status_code=e.status_code,
        )
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": e.message, "status_code": e.status_code},
        )

    except Exception as e:
        logger.error("Error inesperado al eliminar marcaciones por filtro", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": "Error interno del servidor", "detail": str(e)},
        )


@router.delete("/por-id")
async def eliminar_marcaciones_por_id(
    service: MarcacionesDependencia,
    sincronizacion: SincronizacionDependencia,
    id_marcacion: str = Query(..., description="ID de la marcación")
):
    """
    Elimina las marcaciones de un empleado desde BioTime.

    Args:
        service: Servicio de BioTime inyectado
        codigo_empleado: Código del empleado

    Returns:
        Lista de marcaciones por empleado

    Raises:
        HTTPException: Si hay error al obtener los marcaciones por empleado
    """
    try:
        logger.info("DELETE /marcaciones/por-id", id_marcacion=id_marcacion)
        await service.eliminar_marcaciones_por_id(id_marcacion=id_marcacion)
        await sincronizacion.sincronizar()
        return {"message": "Marcación eliminada exitosamente", "id": id_marcacion}

    except BioTimeException as e:
        logger.error(
            "Error de BioTime al eliminar marcaciones por ID de maración",
            error=e.message,
            status_code=e.status_code,
        )
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": e.message, "status_code": e.status_code},
        )

    except Exception as e:
        logger.error("Error inesperado al eliminar marcaciones por ID de marcación", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": "Error interno del servidor", "detail": str(e)},
        )
