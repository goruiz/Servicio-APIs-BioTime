"""
Endpoints de áreas de BioTime.
"""
from typing import List

from fastapi import APIRouter, HTTPException, Query

from app.api.dependencias import AreasDependencia
from app.core.exceptions import BioTimeException
from app.schemas.areas.respuesta_areas import AreaDto
from app.utils.routing import ConfigurableAliasRoute

router = APIRouter(prefix="/areas", tags=["Areas"], route_class=ConfigurableAliasRoute)


@router.get("", response_model=List[AreaDto])
async def obtener_areas(
    service: AreasDependencia,
    page: int = Query(default=1, ge=1, description="Número de página"),
    page_size: int = Query(default=10, ge=1, le=100, description="Tamaño de página"),
):
    """Obtiene la lista paginada de áreas registradas en BioTime."""
    try:
        result = await service.obtener_areas(page=page, page_size=page_size)
        return result.data

    except BioTimeException as e:
        print(f"[Area] ERROR - GET /areas: {e.message} (HTTP {e.status_code})")
        raise HTTPException(status_code=e.status_code, detail={"error": e.message, "status_code": e.status_code})

    except Exception as e:
        print(f"[Area] ERROR - GET /areas: {e}")
        raise HTTPException(status_code=500, detail={"error": "Error interno del servidor", "detail": str(e)})


@router.get("/{area_id}", response_model=AreaDto)
async def obtener_area_por_id(
    service: AreasDependencia,
    area_id: int,
):
    """Obtiene un área por su ID interno de BioTime."""
    try:
        return await service.obtener_area_por_id(area_id=area_id)

    except BioTimeException as e:
        print(f"[Area] ERROR - GET /areas/{area_id}: {e.message} (HTTP {e.status_code})")
        raise HTTPException(status_code=e.status_code, detail={"error": e.message, "status_code": e.status_code})

    except Exception as e:
        print(f"[Area] ERROR - GET /areas/{area_id}: {e}")
        raise HTTPException(status_code=500, detail={"error": "Error interno del servidor", "detail": str(e)})
