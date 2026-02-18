"""
Endpoints de empleados.
"""
from fastapi import APIRouter, HTTPException, Query

from app.api.dependencies import  MarcacionesDependencia
from app.core.exceptions import BioTimeException
from app.core.logging import get_logger
from typing import List

from app.schemas.marcaciones.respuesta_marcaciones import MarcacionesDto

logger = get_logger(__name__)
router = APIRouter(prefix="/marcaciones", tags=["Marcaciones"])


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
