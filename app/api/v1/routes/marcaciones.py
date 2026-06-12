"""
Endpoints de marcaciones.
"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.api.dependencias import MarcacionesDependencia, SincronizacionDependencia
from app.clients.preciso_client import PrecisoClient, PrecisoConnectionError
from app.core.exceptions import BioTimeException
from app.schemas.tareas.tarea import CompletarTarea
from app.schemas.marcaciones.respuesta_marcaciones import MarcacionesDto
from app.utils.routing import ConfigurableAliasRoute

router = APIRouter(prefix="/marcaciones", tags=["Marcaciones"], route_class=ConfigurableAliasRoute)


@router.get("", response_model=List[MarcacionesDto])
async def obtener_marcaciones(
    service: MarcacionesDependencia,
    page: int = Query(default=1, ge=1, description="Número de página"),
    page_size: int = Query(default=10, ge=1, le=100, description="Tamaño de página"),
):
    """Obtiene la lista paginada de marcaciones desde BioTime."""
    try:
        result = await service.obtener_marcaciones(page=page, page_size=page_size)
        return result.data

    except BioTimeException as e:
        print(f"[Marcaciones] ERROR - GET /marcaciones: {e.message} (HTTP {e.status_code})")
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": e.message, "status_code": e.status_code},
        )

    except Exception as e:
        print(f"[Marcaciones] ERROR - GET /marcaciones: {e}")
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
    """Obtiene la lista paginada de marcaciones desde BioTime por empleado."""
    try:
        result = await service.obtener_marcaciones_por_empleado(
            codigo_empleado=codigo_empleado,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            page=page,
            page_size=page_size,
        )
        return result.data

    except BioTimeException as e:
        print(f"[Marcaciones] ERROR - GET /marcaciones/por-empleado emp_code={codigo_empleado}: {e.message} (HTTP {e.status_code})")
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": e.message, "status_code": e.status_code},
        )

    except Exception as e:
        print(f"[Marcaciones] ERROR - GET /marcaciones/por-empleado emp_code={codigo_empleado}: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Error interno del servidor", "detail": str(e)},
        )


@router.get("/por-terminal", response_model=List[MarcacionesDto])
async def obtener_marcaciones_por_terminal(
    service: MarcacionesDependencia,
    terminal_sn: str = Query(..., description="Número de serie del terminal (SN)"),
    fecha_inicio: Optional[str] = Query(default=None, description="Fecha de inicio (ej: 2024-01-01 00:00:00)"),
    fecha_fin: Optional[str] = Query(default=None, description="Fecha de fin (ej: 2024-01-31 23:59:59)"),
    page: int = Query(default=1, ge=1, description="Número de página"),
    page_size: int = Query(default=10, ge=1, le=100, description="Tamaño de página"),
):
    """Obtiene la lista paginada de marcaciones desde BioTime por número de serie del terminal."""
    try:
        result = await service.obtener_marcaciones_por_serial(
            terminal_sn=terminal_sn,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            page=page,
            page_size=page_size,
        )
        return result.data

    except BioTimeException as e:
        print(f"[Marcaciones] ERROR - GET /marcaciones/por-terminal sn={terminal_sn}: {e.message} (HTTP {e.status_code})")
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": e.message, "status_code": e.status_code},
        )

    except Exception as e:
        print(f"[Marcaciones] ERROR - GET /marcaciones/por-terminal sn={terminal_sn}: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Error interno del servidor", "detail": str(e)},
        )


@router.get("/por-ip", response_model=List[MarcacionesDto])
async def obtener_marcaciones_por_ip(
    service: MarcacionesDependencia,
    ip_terminal: str = Query(..., description="Dirección IP del terminal (ej: 192.168.1.10)"),
    fecha_inicio: Optional[str] = Query(default=None, description="Fecha de inicio (ej: 2024-01-01 00:00:00)"),
    fecha_fin: Optional[str] = Query(default=None, description="Fecha de fin (ej: 2024-01-31 23:59:59)"),
    page: int = Query(default=1, ge=1, description="Número de página"),
    page_size: int = Query(default=10, ge=1, le=100, description="Tamaño de página"),
):
    """
    Obtiene la lista paginada de marcaciones de un terminal por su dirección IP.

    - Sin fechas: retorna todas las marcaciones del terminal.
    - Solo fecha_inicio: desde esa fecha hasta la más reciente.
    - Solo fecha_fin: desde el inicio de los registros hasta esa fecha.
    - Ambas fechas: rango exacto.
    """
    try:
        result = await service.obtener_marcaciones_por_ip(
            ip_terminal=ip_terminal,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            page=page,
            page_size=page_size,
        )
        return result.data

    except BioTimeException as e:
        print(f"[Marcaciones] ERROR - GET /marcaciones/por-ip ip={ip_terminal}: {e.message} (HTTP {e.status_code})")
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": e.message, "status_code": e.status_code},
        )

    except Exception as e:
        print(f"[Marcaciones] ERROR - GET /marcaciones/por-ip ip={ip_terminal}: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Error interno del servidor", "detail": str(e)},
        )


@router.post("/recuperar-en-preciso")
async def recuperar_marcaciones_en_preciso(
    service: MarcacionesDependencia,
    id_tarea: int = Query(..., description="ID de la tarea EMPMAR pendiente en Preciso"),
    terminal_sn: str = Query(..., description="Número de serie del terminal (ej: NYU7251800550)"),
    fecha_inicio: Optional[str] = Query(default=None, description="Fecha de inicio (ej: 2024-01-01 00:00:00). Sin valor: desde el inicio de los registros"),
    fecha_fin: Optional[str] = Query(default=None, description="Fecha de fin (ej: 2024-01-31 23:59:59). Sin valor: hasta la más reciente"),
):
    """
    Recupera marcaciones de BioTime y las envía a Preciso como respuesta a una tarea EMPMAR.

    Útil para copiar marcaciones históricas que Preciso no recibió en su momento.
    El id_tarea debe corresponder a una tarea EMPMAR pendiente en Preciso.
    """
    try:
        marcaciones = await service.obtener_marcaciones_por_terminal(
            terminal_sn=terminal_sn,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )

        if not marcaciones:
            return {"enviadas": 0, "mensaje": "No se encontraron marcaciones para los filtros indicados"}

        respuesta = "&".join(f"{m.emp_code}|{m.punch_time}" for m in marcaciones)

        preciso = PrecisoClient()
        await preciso.completar_tarea(
            CompletarTarea(id_tarea=id_tarea, instruccion="EMPMAR", respuesta=respuesta)
        )

        print(f"[Recuperar] Enviadas {len(marcaciones)} marcaciones a Preciso — id_tarea={id_tarea} SN={terminal_sn}")
        return {"enviadas": len(marcaciones), "id_tarea": id_tarea}

    except PrecisoConnectionError as e:
        print(f"[Recuperar] ERROR Preciso — id_tarea={id_tarea}: {e}")
        raise HTTPException(status_code=502, detail={"error": str(e)})

    except BioTimeException as e:
        print(f"[Recuperar] ERROR BioTime — id_tarea={id_tarea}: {e.message} (HTTP {e.status_code})")
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": e.message, "status_code": e.status_code},
        )

    except Exception as e:
        print(f"[Recuperar] ERROR — id_tarea={id_tarea}: {e}")
        raise HTTPException(status_code=500, detail={"error": "Error interno del servidor", "detail": str(e)})


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
        eliminadas = await service.eliminar_marcaciones(
            codigo_empleado=codigo_empleado,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )
        await sincronizacion.sincronizar()
        return {"message": "Marcaciones eliminadas exitosamente", "eliminadas": eliminadas}

    except BioTimeException as e:
        print(f"[Marcaciones] ERROR - DELETE /marcaciones/por-filtro: {e.message} (HTTP {e.status_code})")
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": e.message, "status_code": e.status_code},
        )

    except Exception as e:
        print(f"[Marcaciones] ERROR - DELETE /marcaciones/por-filtro: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Error interno del servidor", "detail": str(e)},
        )


@router.delete("/por-id")
async def eliminar_marcaciones_por_id(
    service: MarcacionesDependencia,
    sincronizacion: SincronizacionDependencia,
    id_marcacion: str = Query(..., description="ID de la marcación"),
):
    """Elimina una marcación por su ID."""
    try:
        await service.eliminar_marcaciones_por_id(id_marcacion=id_marcacion)
        await sincronizacion.sincronizar()
        return {"message": "Marcación eliminada exitosamente", "id": id_marcacion}

    except BioTimeException as e:
        print(f"[Marcaciones] ERROR - DELETE /marcaciones/por-id ID={id_marcacion}: {e.message} (HTTP {e.status_code})")
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": e.message, "status_code": e.status_code},
        )

    except Exception as e:
        print(f"[Marcaciones] ERROR - DELETE /marcaciones/por-id ID={id_marcacion}: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Error interno del servidor", "detail": str(e)},
        )
