"""
Servicio de marcaciones.
Lógica de negocio para interactuar con el recurso de transacciones de BioTime.
"""
from typing import Optional

from app.clients.biotime_client import BioTimeClient
from app.core.logging import get_logger
from app.interfaces.marcaciones.interface_marcaciones import IMarcaciones
from app.schemas.biotime.common import PaginatedResponse
from app.schemas.marcaciones.respuesta_marcaciones import MarcacionesDto

logger = get_logger(__name__)


class ServicioMarcaciones(IMarcaciones):
    """Implementación del servicio de marcaciones."""

    def __init__(self, client: BioTimeClient):
        self._client = client

    async def obtener_marcaciones(
        self, page: int = 1, page_size: int = 10
    ) -> PaginatedResponse[MarcacionesDto]:
        """Obtiene la lista paginada de marcaciones desde BioTime."""
        logger.info("Obteniendo marcaciones", page=page, page_size=page_size)
        params = {"page": page, "page_size": page_size}
        response_data = await self._client.get("iclock/api/transactions/", params=params)
        marcaciones = [MarcacionesDto(**marc) for marc in response_data.get("data", [])]
        result = PaginatedResponse[MarcacionesDto](
            count=response_data.get("count", 0),
            next=response_data.get("next"),
            previous=response_data.get("previous"),
            data=marcaciones,
        )
        logger.info(
            "Marcaciones obtenidas exitosamente",
            total=result.count,
            page=page,
            returned=len(marcaciones),
        )
        return result

    async def obtener_marcaciones_por_empleado(
        self,
        codigo_empleado: str,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> PaginatedResponse[MarcacionesDto]:
        """Obtiene marcaciones filtradas por empleado y rango de fechas."""
        logger.info(
            "Obteniendo marcaciones por empleado",
            codigo_empleado=codigo_empleado,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            page=page,
            page_size=page_size,
        )
        params: dict = {"emp_code": codigo_empleado, "page": page, "page_size": page_size}
        if fecha_inicio is not None:
            params["start_time"] = fecha_inicio
        if fecha_fin is not None:
            params["end_time"] = fecha_fin

        response_data = await self._client.get("iclock/api/transactions/", params=params)
        marcaciones = [MarcacionesDto(**marc) for marc in response_data.get("data", [])]
        result = PaginatedResponse[MarcacionesDto](
            count=response_data.get("count", 0),
            next=response_data.get("next"),
            previous=response_data.get("previous"),
            data=marcaciones,
        )
        logger.info(
            "Marcaciones por empleado obtenidas exitosamente",
            total=result.count,
            page=page,
            returned=len(marcaciones),
        )
        return result

    async def eliminar_marcaciones_por_id(self, id_marcacion: str) -> None:
        """
        Elimina una marcación por su ID.

        Args:
            id_marcacion: ID de la transacción a eliminar
        """
        logger.info("Eliminando marcación por ID", id=id_marcacion)
        await self._client.delete(f"iclock/api/transactions/{id_marcacion}/")
        logger.info("Marcación eliminada exitosamente", id=id_marcacion)

    async def eliminar_marcaciones(
        self,
        codigo_empleado: Optional[str] = None,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
    ) -> int:
        """
        Elimina marcaciones filtrando por empleado y/o rango de fechas.

        Pagina el GET de BioTime para recolectar todos los IDs que coincidan
        con los filtros y los elimina uno a uno.
        """
        logger.info(
            "Iniciando eliminación masiva de marcaciones",
            codigo_empleado=codigo_empleado,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )

        # Construir parámetros de filtro para el GET
        params: dict = {"page_size": 100}
        if codigo_empleado is not None:
            params["emp_code"] = codigo_empleado
        if fecha_inicio is not None:
            params["start_time"] = fecha_inicio
        if fecha_fin is not None:
            params["end_time"] = fecha_fin

        # Paginar para recolectar todos los IDs que coincidan
        ids_a_eliminar: list[int] = []
        page = 1
        while True:
            params["page"] = page
            response_data = await self._client.get("iclock/api/transactions/", params=params)
            data = response_data.get("data", [])
            ids_a_eliminar.extend(item["id"] for item in data)

            if not response_data.get("next"):
                break
            page += 1

        logger.info("IDs recolectados para eliminar", total=len(ids_a_eliminar))

        # Eliminar uno a uno
        for id_marcacion in ids_a_eliminar:
            await self._client.delete(f"iclock/api/transactions/{id_marcacion}/")

        logger.info("Eliminación masiva completada", eliminadas=len(ids_a_eliminar))
        return len(ids_a_eliminar)
