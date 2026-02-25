"""
Endpoints de huellas dactilares.
"""
from typing import List

from fastapi import APIRouter, HTTPException, Query

from app.api.dependencias import HuellasDependencia
from app.core.exceptions import BioTimeException
from app.schemas.huellas.respuesta_huellas import HuellaDto
from app.utils.routing import ConfigurableAliasRoute

router = APIRouter(prefix="/huellas", tags=["Huellas"], route_class=ConfigurableAliasRoute)


@router.get("", response_model=List[HuellaDto])
async def obtener_huellas(
    service: HuellasDependencia,
    page: int = Query(default=1, ge=1, description="Número de página"),
    page_size: int = Query(default=10, ge=1, le=100, description="Tamaño de página"),
):
    """Obtiene la lista paginada de todas las huellas dactilares registradas en BioTime."""
    try:
        result = await service.obtener_huellas(page=page, page_size=page_size)
        return result.data

    except BioTimeException as e:
        print(f"[Huellas] ERROR - GET /huellas: {e.message} (HTTP {e.status_code})")
        raise HTTPException(status_code=e.status_code, detail={"error": e.message, "status_code": e.status_code})

    except Exception as e:
        print(f"[Huellas] ERROR - GET /huellas: {e}")
        raise HTTPException(status_code=500, detail={"error": "Error interno del servidor", "detail": str(e)})


@router.get("/por-empleado", response_model=List[HuellaDto])
async def obtener_huellas_por_empleado(
    service: HuellasDependencia,
    empleado_id: int = Query(..., description="ID del empleado (employee_id en iclock_biodata)"),
    page: int = Query(default=1, ge=1, description="Número de página"),
    page_size: int = Query(default=10, ge=1, le=100, description="Tamaño de página"),
):
    """Obtiene las huellas dactilares registradas de un empleado específico por su ID."""
    try:
        result = await service.obtener_huellas_por_empleado(
            empleado_id=empleado_id, page=page, page_size=page_size
        )
        return result.data

    except BioTimeException as e:
        print(f"[Huellas] ERROR - GET /huellas/por-empleado ID={empleado_id}: {e.message} (HTTP {e.status_code})")
        raise HTTPException(status_code=e.status_code, detail={"error": e.message, "status_code": e.status_code})

    except Exception as e:
        print(f"[Huellas] ERROR - GET /huellas/por-empleado ID={empleado_id}: {e}")
        raise HTTPException(status_code=500, detail={"error": "Error interno del servidor", "detail": str(e)})
