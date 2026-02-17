"""
Endpoints de empleados.
"""
from fastapi import APIRouter, HTTPException, Query

from app.api.dependencies import BioTimeServiceDep
from app.core.exceptions import BioTimeException
from app.core.logging import get_logger
from app.schemas.biotime.common import PaginatedResponse
from app.schemas.biotime.employee import EmployeeDto

logger = get_logger(__name__)
router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("", response_model=PaginatedResponse[EmployeeDto])
async def get_employees(
    service: BioTimeServiceDep,
    page: int = Query(default=1, ge=1, description="Número de página"),
    page_size: int = Query(default=10, ge=1, le=100, description="Tamaño de página"),
):
    """
    Obtiene la lista paginada de empleados desde BioTime.

    Args:
        service: Servicio de BioTime inyectado
        page: Número de página (mínimo 1)
        page_size: Cantidad de registros por página (1-100)

    Returns:
        Lista paginada de empleados

    Raises:
        HTTPException: Si hay error al obtener los empleados
    """
    try:
        logger.info("GET /employees", page=page, page_size=page_size)
        result = await service.get_employees(page=page, page_size=page_size)
        return result

    except BioTimeException as e:
        logger.error(
            "Error de BioTime al obtener empleados",
            error=e.message,
            status_code=e.status_code,
        )
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": e.message, "status_code": e.status_code},
        )

    except Exception as e:
        logger.error("Error inesperado al obtener empleados", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": "Error interno del servidor", "detail": str(e)},
        )
