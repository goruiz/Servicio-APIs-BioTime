"""
Endpoints de terminales biométricos.
"""
from typing import List

from fastapi import APIRouter, HTTPException, Query

from app.api.dependencias import TerminalesDependencia
from app.core.exceptions import BioTimeException
from app.schemas.terminales.respuesta_terminales import TerminalDto
from app.utils.routing import ConfigurableAliasRoute

router = APIRouter(prefix="/terminales", tags=["Terminales"], route_class=ConfigurableAliasRoute)


@router.get("", response_model=List[TerminalDto])
async def obtener_terminales(
    service: TerminalesDependencia,
    page: int = Query(default=1, ge=1, description="Número de página"),
    page_size: int = Query(default=10, ge=1, le=100, description="Tamaño de página"),
):
    """Obtiene la lista paginada de terminales biométricos registrados en BioTime."""
    try:
        result = await service.obtener_terminales(page=page, page_size=page_size)
        return result.data

    except BioTimeException as e:
        print(f"[Terminal] ERROR - GET /terminales: {e.message} (HTTP {e.status_code})")
        raise HTTPException(status_code=e.status_code, detail={"error": e.message, "status_code": e.status_code})

    except Exception as e:
        print(f"[Terminal] ERROR - GET /terminales: {e}")
        raise HTTPException(status_code=500, detail={"error": "Error interno del servidor", "detail": str(e)})


@router.get("/por-sn", response_model=TerminalDto)
async def obtener_terminal_por_sn(
    service: TerminalesDependencia,
    sn: str = Query(..., description="Número de serie del terminal (coincide con terminal_sn en marcaciones)"),
):
    """Obtiene un terminal por su número de serie. Útil para saber a qué tienda/lugar pertenece un dispositivo."""
    try:
        return await service.obtener_terminal_por_sn(sn=sn)

    except BioTimeException as e:
        print(f"[Terminal] ERROR - GET /terminales/por-sn SN={sn}: {e.message} (HTTP {e.status_code})")
        raise HTTPException(status_code=e.status_code, detail={"error": e.message, "status_code": e.status_code})

    except Exception as e:
        print(f"[Terminal] ERROR - GET /terminales/por-sn SN={sn}: {e}")
        raise HTTPException(status_code=500, detail={"error": "Error interno del servidor", "detail": str(e)})


@router.get("/{terminal_id}", response_model=TerminalDto)
async def obtener_terminal_por_id(
    service: TerminalesDependencia,
    terminal_id: int,
):
    """Obtiene un terminal biométrico por su ID interno de BioTime."""
    try:
        return await service.obtener_terminal_por_id(terminal_id=terminal_id)

    except BioTimeException as e:
        print(f"[Terminal] ERROR - GET /terminales/{terminal_id}: {e.message} (HTTP {e.status_code})")
        raise HTTPException(status_code=e.status_code, detail={"error": e.message, "status_code": e.status_code})

    except Exception as e:
        print(f"[Terminal] ERROR - GET /terminales/{terminal_id}: {e}")
        raise HTTPException(status_code=500, detail={"error": "Error interno del servidor", "detail": str(e)})
