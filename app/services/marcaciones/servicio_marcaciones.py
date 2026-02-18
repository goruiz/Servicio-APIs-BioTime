"""
Implementación del servicio de BioTime.
Contiene la lógica de negocio para interactuar con BioTime.
"""
from typing import Optional

from app.clients.biotime_client import BioTimeClient
from app.core.logging import get_logger
from app.interfaces.marcaciones.interface_marcaciones import IMarcaciones
from app.schemas.biotime.common import PaginatedResponse
from app.schemas.marcaciones.respuesta_marcaciones import MarcacionesDto

logger = get_logger(__name__)


class ServicioMarcaciones(IMarcaciones):
    """Implementación del servicio de BioTime."""

    def __init__(self, client: BioTimeClient):
        """
        Inicializa el servicio con un cliente de BioTime.

        Args:
            client: Cliente HTTP de BioTime
        """
        self._client = client

    async def obtener_marcaciones(
        self, page: int = 1, page_size: int = 10
    ) -> PaginatedResponse[MarcacionesDto]:
        """
        Obtiene la lista paginada de marcaciones desde BioTime.

        Args:
            page: Número de página (inicia en 1)
            page_size: Cantidad de registros por página

        Returns:
            PaginatedResponse con la lista de marcaciones
        """
        logger.info("Obteniendo marcaciones", page=page, page_size=page_size)

        params = {"page": page, "page_size": page_size}
        response_data = await self._client.get("iclock/api/transactions/?emp_code=**&start_time=**&end_time=**", params=params)

        # Parsear respuesta a nuestros modelos
        marcaciones = [MarcacionesDto(**marc) for marc in response_data.get("data", [])]

        paginated_response = PaginatedResponse[MarcacionesDto](
            count=response_data.get("count", 0),
            next=response_data.get("next"),
            previous=response_data.get("previous"),
            data=marcaciones,
        )

        logger.info(
            "Marcaciones obtenidos exitosamente",
            total=paginated_response.count,
            page=page,
            returned=len(marcaciones),
        )

        return paginated_response

    async def obtener_marcaciones_por_empleado(
        self, codigo_empleado: str, fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None, page: int = 1, page_size: int = 10
    ) -> PaginatedResponse[MarcacionesDto]:
        """
        Obtiene la lista paginada de marcaciones desde BioTime por empleado.

        Args:
            codigo_empleado: Código del empleado
            fecha_inicio: Fecha de inicio del rango (opcional)
            fecha_fin: Fecha de fin del rango (opcional)
            page: Número de página (inicia en 1)
            page_size: Cantidad de registros por página

        Returns:
            PaginatedResponse con la lista de marcaciones
        """
        logger.info("Obteniendo marcaciones", codigo_empleado=codigo_empleado, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, page=page, page_size=page_size)

        start_time = fecha_inicio if fecha_inicio is not None else "**"
        end_time = fecha_fin if fecha_fin is not None else "**"

        params = {"page": page, "page_size": page_size}
        response_data = await self._client.get(f"iclock/api/transactions/?emp_code={codigo_empleado}&start_time={start_time}&end_time={end_time}", params=params)

        # Parsear respuesta a nuestros modelos
        marcaciones = [MarcacionesDto(**marc) for marc in response_data.get("data", [])]

        paginated_response = PaginatedResponse[MarcacionesDto](
            count=response_data.get("count", 0),
            next=response_data.get("next"),
            previous=response_data.get("previous"),
            data=marcaciones,
        )

        logger.info(
            "Marcaciones obtenidos exitosamente",
            total=paginated_response.count,
            page=page,
            returned=len(marcaciones),
        )

        return paginated_response
