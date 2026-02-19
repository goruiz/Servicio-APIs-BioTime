"""
Servicio de huellas dactilares.
Lógica de negocio para interactuar con el recurso userfingerprint de BioTime.
"""
from app.clients.biotime_client import BioTimeClient
from app.core.config import settings
from app.core.logging import get_logger
from app.interfaces.huellas.interface_huellas import IHuellas
from app.schemas.biotime.common import PaginatedResponse
from app.schemas.huellas.respuesta_huellas import HuellaDto

logger = get_logger(__name__)


class ServicioHuellas(IHuellas):
    """Implementación del servicio de huellas dactilares."""

    def __init__(self, client: BioTimeClient):
        self._client = client

    async def obtener_huellas(
        self, page: int = 1, page_size: int = 10
    ) -> PaginatedResponse[HuellaDto]:
        """Obtiene la lista paginada de todas las huellas registradas."""
        logger.info("Obteniendo huellas", page=page, page_size=page_size)
        params = {"page": page, "page_size": page_size}
        response_data = await self._client.get(settings.BIOTIME_ENDPOINT_HUELLAS, params=params)
        huellas = [HuellaDto(**h) for h in response_data.get("data", [])]
        result = PaginatedResponse[HuellaDto](
            count=response_data.get("count", 0),
            next=response_data.get("next"),
            previous=response_data.get("previous"),
            data=huellas,
        )
        logger.info("Huellas obtenidas exitosamente", total=result.count, returned=len(huellas))
        return result

    async def obtener_huellas_por_empleado(
        self, codigo_empleado: str, page: int = 1, page_size: int = 10
    ) -> PaginatedResponse[HuellaDto]:
        """Obtiene las huellas de un empleado específico."""
        logger.info("Obteniendo huellas por empleado", codigo_empleado=codigo_empleado, page=page, page_size=page_size)
        params = {"emp_code": codigo_empleado, "page": page, "page_size": page_size}
        response_data = await self._client.get(settings.BIOTIME_ENDPOINT_HUELLAS, params=params)
        huellas = [HuellaDto(**h) for h in response_data.get("data", [])]
        result = PaginatedResponse[HuellaDto](
            count=response_data.get("count", 0),
            next=response_data.get("next"),
            previous=response_data.get("previous"),
            data=huellas,
        )
        logger.info(
            "Huellas por empleado obtenidas exitosamente",
            codigo_empleado=codigo_empleado,
            total=result.count,
            returned=len(huellas),
        )
        return result
