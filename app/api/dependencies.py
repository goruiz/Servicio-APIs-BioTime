"""
Dependencias compartidas de FastAPI.
Provee instancias de servicios mediante inyección de dependencias.
"""
from typing import Annotated

from fastapi import Depends

from app.clients.biotime_client import BioTimeClient
from app.services.biotime_service import BioTimeService
from app.interfaces.interface_biotime_service import IBioTimeService


def get_biotime_client() -> BioTimeClient:
    """
    Provee una instancia del cliente de BioTime.

    Returns:
        Cliente de BioTime
    """
    return BioTimeClient()


def get_biotime_service(
    client: Annotated[BioTimeClient, Depends(get_biotime_client)]
) -> IBioTimeService:
    """
    Provee una instancia del servicio de BioTime.

    Args:
        client: Cliente de BioTime inyectado

    Returns:
        Servicio de BioTime
    """
    return BioTimeService(client=client)


# Type aliases para usar en los endpoints
BioTimeServiceDependencia = Annotated[IBioTimeService, Depends(get_biotime_service)]
