"""
Dependencias compartidas de FastAPI.
Provee instancias de servicios mediante inyección de dependencias.
"""
from typing import Annotated

from fastapi import Depends

from app.clients.biotime_client import BioTimeClient
from app.core.config import settings
from app.db.conexion import obtener_pool
from app.db.repositorios.repositorio_huellas import RepositorioHuellas
from app.interfaces.empleado.interface_empleado import IEmpleado
from app.interfaces.huellas.interface_huellas import IHuellas
from app.interfaces.marcaciones.interface_marcaciones import IMarcaciones
from app.interfaces.sincronizacion.interface_sincronizacion import (
    ISincronizacion,
    SincronizacionDeshabilitada,
)
from app.interfaces.terminales.interface_terminales import ITerminales
from app.services.empleado.servicio_empleado import ServicioEmpleado
from app.services.huellas.servicio_huellas import ServicioHuellas
from app.services.marcaciones.servicio_marcaciones import ServicioMarcaciones
from app.services.sincronizacion.servicio_sincronizacion import ServicioSincronizacion
from app.services.terminales.servicio_terminales import ServicioTerminales


def get_biotime_client() -> BioTimeClient:
    """
    Provee una instancia del cliente de BioTime.

    Returns:
        Cliente de BioTime
    """
    return BioTimeClient()


def obtener_servicio_empleados(
    client: Annotated[BioTimeClient, Depends(get_biotime_client)]
) -> IEmpleado:
    """
    Provee una instancia del servicio de BioTime.

    Args:
        client: Cliente de BioTime inyectado

    Returns:
        Servicio de BioTime
    """
    return ServicioEmpleado(client=client)

def obtener_servicio_marcaciones(
    client: Annotated[BioTimeClient, Depends(get_biotime_client)]
) -> IMarcaciones:
    """
    Provee una instancia del servicio de BioTime.

    Args:
        client: Cliente de BioTime inyectado

    Returns:
        Servicio de BioTime
    """
    return ServicioMarcaciones(client=client)


def obtener_servicio_huellas() -> IHuellas:
    repositorio = RepositorioHuellas(pool=obtener_pool())
    return ServicioHuellas(repositorio=repositorio)


def obtener_servicio_sincronizacion(
    client: Annotated[BioTimeClient, Depends(get_biotime_client)]
) -> ISincronizacion:
    """
    Devuelve ServicioSincronizacion si BIOTIME_SYNC_HABILITADO=True,
    o SincronizacionDeshabilitada (Null Object) si está en False.
    Para apagar la sincronización basta con cambiar el valor en .env.
    """
    if settings.BIOTIME_SYNC_HABILITADO:
        return ServicioSincronizacion(client=client)
    return SincronizacionDeshabilitada()


def obtener_servicio_terminales(
    client: Annotated[BioTimeClient, Depends(get_biotime_client)]
) -> ITerminales:
    """Provee una instancia del servicio de terminales."""
    return ServicioTerminales(client=client)


# Type aliases para usar en los endpoints
EmpleadoDependencia = Annotated[IEmpleado, Depends(obtener_servicio_empleados)]
HuellasDependencia = Annotated[IHuellas, Depends(obtener_servicio_huellas)]
MarcacionesDependencia = Annotated[IMarcaciones, Depends(obtener_servicio_marcaciones)]
SincronizacionDependencia = Annotated[ISincronizacion, Depends(obtener_servicio_sincronizacion)]
TerminalesDependencia = Annotated[ITerminales, Depends(obtener_servicio_terminales)]
