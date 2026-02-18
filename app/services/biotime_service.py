"""
Implementación del servicio de BioTime.
Contiene la lógica de negocio para interactuar con BioTime.
"""
from app.clients.biotime_client import BioTimeClient
from app.core.logging import get_logger
from app.schemas.biotime.common import PaginatedResponse
from app.schemas.biotime.employee import EmployeeDto
from app.interfaces.interface_biotime_service import IBioTimeService

logger = get_logger(__name__)


class BioTimeService(IBioTimeService):
    """Implementación del servicio de BioTime."""

    def __init__(self, client: BioTimeClient):
        """
        Inicializa el servicio con un cliente de BioTime.

        Args:
            client: Cliente HTTP de BioTime
        """
        self._client = client

    async def get_employees(
        self, page: int = 1, page_size: int = 10
    ) -> PaginatedResponse[EmployeeDto]:
        """
        Obtiene la lista paginada de empleados desde BioTime.

        Args:
            page: Número de página (inicia en 1)
            page_size: Cantidad de registros por página

        Returns:
            PaginatedResponse con la lista de empleados
        """
        logger.info("Obteniendo empleados", page=page, page_size=page_size)

        params = {"page": page, "page_size": page_size}
        response_data = await self._client.get("personnel/api/employees/", params=params)

        # Parsear respuesta a nuestros modelos
        employees = [EmployeeDto(**emp) for emp in response_data.get("data", [])]

        paginated_response = PaginatedResponse[EmployeeDto](
            count=response_data.get("count", 0),
            next=response_data.get("next"),
            previous=response_data.get("previous"),
            data=employees,
        )

        logger.info(
            "Empleados obtenidos exitosamente",
            total=paginated_response.count,
            page=page,
            returned=len(employees),
        )

        return paginated_response
