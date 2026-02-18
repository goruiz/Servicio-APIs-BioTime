"""
Dependencias compartidas de FastAPI.
Provee instancias de servicios mediante inyección de dependencias.
"""
from typing import Annotated

from fastapi import Depends

from app.clients.biotime_client import BioTimeClient
from app.services.empleado.servicio_empleado import ServicioEmpleado
from app.services.marcaciones.servicio_marcaciones import ServicioMarcaciones
from app.interfaces.empleado.interface_empleado import IEmpleado
from app.interfaces.marcaciones.interface_marcaciones import IMarcaciones


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


# Type aliases para usar en los endpoints
EmpleadoDependencia = Annotated[IEmpleado, Depends(obtener_servicio_empleados)]
MarcacionesDependencia = Annotated[IMarcaciones, Depends(obtener_servicio_empleados)]
