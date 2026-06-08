"""
Endpoints de huellas dactilares.
"""
from typing import List

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencias import BiodataDependencia, HuellasDependencia
from app.core.exceptions import BioTimeException
from app.schemas.huellas.respuesta_huellas import (
    CopiarHuellaRequest,
    CopiarHuellaResponse,
    EstadoHuellasEmpleadoResponse,
    HuellaDto,
    SincronizarTerminalesRequest,
    SincronizarTerminalesResponse,
)
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


@router.get("/estado-empleado", response_model=EstadoHuellasEmpleadoResponse)
async def obtener_estado_huellas_empleado(
    service: BiodataDependencia,
    emp_code: str = Query(..., description="Código del empleado en BioTime"),
):
    """Indica si un empleado tiene huellas registradas y en qué terminales biométricos están."""
    try:
        return await service.obtener_estado_huellas(emp_code=emp_code)

    except ValueError as e:
        raise HTTPException(status_code=404, detail={"error": str(e)})

    except BioTimeException as e:
        print(f"[Huellas] ERROR - GET /huellas/estado-empleado emp_code={emp_code}: {e.message}")
        raise HTTPException(status_code=e.status_code, detail={"error": e.message, "status_code": e.status_code})

    except Exception as e:
        print(f"[Huellas] ERROR - GET /huellas/estado-empleado emp_code={emp_code}: {e}")
        raise HTTPException(status_code=500, detail={"error": "Error interno del servidor", "detail": str(e)})


@router.get("/por-terminal", response_model=List[HuellaDto])
async def obtener_huellas_por_terminal(
    service: HuellasDependencia,
    sn: str = Query(..., description="Número de serie del terminal biométrico"),
    page: int = Query(default=1, ge=1, description="Número de página"),
    page_size: int = Query(default=10, ge=1, le=100, description="Tamaño de página"),
):
    """Obtiene las huellas dactilares registradas en un terminal biométrico por su número de serie."""
    try:
        result = await service.obtener_huellas_por_terminal(sn=sn, page=page, page_size=page_size)
        return result.data

    except BioTimeException as e:
        print(f"[Huellas] ERROR - GET /huellas/por-terminal SN={sn}: {e.message} (HTTP {e.status_code})")
        raise HTTPException(status_code=e.status_code, detail={"error": e.message, "status_code": e.status_code})

    except Exception as e:
        print(f"[Huellas] ERROR - GET /huellas/por-terminal SN={sn}: {e}")
        raise HTTPException(status_code=500, detail={"error": "Error interno del servidor", "detail": str(e)})


@router.post("/sincronizar-terminales", response_model=SincronizarTerminalesResponse, status_code=status.HTTP_200_OK)
async def sincronizar_terminales(
    body: SincronizarTerminalesRequest,
    service: BiodataDependencia,
):
    """
    Copia todas las huellas de un terminal origen a uno o varios terminales destino.
    Las huellas que ya existan en el destino no se duplican ni se sobreescriben.
    Al finalizar sincroniza cada terminal destino con BioTime.
    """
    try:
        resultado = await service.sincronizar_entre_terminales(
            sn_origen=body.sn_origen,
            sns_destino=body.sns_destino,
        )
        return resultado

    except ValueError as e:
        raise HTTPException(status_code=404, detail={"error": str(e)})

    except BioTimeException as e:
        print(f"[Huellas] ERROR - POST /huellas/sincronizar-terminales: {e.message} (HTTP {e.status_code})")
        raise HTTPException(status_code=e.status_code, detail={"error": e.message, "status_code": e.status_code})

    except Exception as e:
        print(f"[Huellas] ERROR - POST /huellas/sincronizar-terminales: {e}")
        raise HTTPException(status_code=500, detail={"error": "Error interno del servidor", "detail": str(e)})


@router.post("/copiar-a-terminal", response_model=CopiarHuellaResponse, status_code=status.HTTP_200_OK)
async def copiar_huellas_a_terminal(
    body: CopiarHuellaRequest,
    service: BiodataDependencia,
):
    """
    Copia los templates biométricos de un empleado a un terminal específico.
    Equivale a ejecutar EMPHUE + COPHUE en un solo paso: obtiene las huellas
    desde PostgreSQL de BioTime y las registra en el terminal indicado por IP.
    """
    try:
        resultados = await service.copiar_a_terminales(
            emp_code=body.emp_code,
            terminal_ips=body.terminal_ips,
        )
        return CopiarHuellaResponse(
            emp_code=body.emp_code,
            terminales=resultados,
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail={"error": str(e)})

    except BioTimeException as e:
        print(f"[Huellas] ERROR - POST /huellas/copiar-a-terminal: {e.message} (HTTP {e.status_code})")
        raise HTTPException(status_code=e.status_code, detail={"error": e.message, "status_code": e.status_code})

    except Exception as e:
        print(f"[Huellas] ERROR - POST /huellas/copiar-a-terminal: {e}")
        raise HTTPException(status_code=500, detail={"error": "Error interno del servidor", "detail": str(e)})
