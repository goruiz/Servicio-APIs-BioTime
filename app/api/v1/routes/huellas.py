"""
Endpoints de huellas dactilares.
"""
from typing import List

from fastapi import APIRouter, HTTPException, Query

from app.api.dependencias import HuellasDependencia
from app.core.exceptions import BioTimeException
from app.core.logging import get_logger
from app.schemas.huellas.respuesta_huellas import HuellaDto
from app.utils.routing import ConfigurableAliasRoute

logger = get_logger(__name__)
router = APIRouter(prefix="/huellas", tags=["Huellas"], route_class=ConfigurableAliasRoute)


@router.get("", response_model=List[HuellaDto])
async def obtener_huellas(
    service: HuellasDependencia,
    page: int = Query(default=1, ge=1, description="Número de página"),
    page_size: int = Query(default=10, ge=1, le=100, description="Tamaño de página"),
):
    """Obtiene la lista paginada de todas las huellas dactilares registradas en BioTime."""
    try:
        logger.info("GET /huellas", page=page, page_size=page_size)
        result = await service.obtener_huellas(page=page, page_size=page_size)
        return result.data

    except BioTimeException as e:
        logger.error("Error de BioTime al obtener huellas", error=e.message, status_code=e.status_code)
        raise HTTPException(status_code=e.status_code, detail={"error": e.message, "status_code": e.status_code})

    except Exception as e:
        logger.error("Error inesperado al obtener huellas", error=str(e))
        raise HTTPException(status_code=500, detail={"error": "Error interno del servidor", "detail": str(e)})


@router.get("/por-empleado", response_model=List[HuellaDto])
async def obtener_huellas_por_empleado(
    service: HuellasDependencia,
    codigo_empleado: str = Query(..., description="Código del empleado (emp_code en BioTime)"),
    page: int = Query(default=1, ge=1, description="Número de página"),
    page_size: int = Query(default=10, ge=1, le=100, description="Tamaño de página"),
):
    """Obtiene las huellas dactilares registradas de un empleado específico."""
    try:
        logger.info("GET /huellas/por-empleado", codigo_empleado=codigo_empleado, page=page, page_size=page_size)
        result = await service.obtener_huellas_por_empleado(
            codigo_empleado=codigo_empleado, page=page, page_size=page_size
        )
        return result.data

    except BioTimeException as e:
        logger.error("Error de BioTime al obtener huellas por empleado", error=e.message, status_code=e.status_code)
        raise HTTPException(status_code=e.status_code, detail={"error": e.message, "status_code": e.status_code})

    except Exception as e:
        logger.error("Error inesperado al obtener huellas por empleado", error=str(e))
        raise HTTPException(status_code=500, detail={"error": "Error interno del servidor", "detail": str(e)})
