"""
Servicio de sincronización de terminales biométricos.
Replica la lógica del proyecto C# de referencia:
  - Pagina todos los terminales desde iclock/api/terminals/
  - Por cada terminal prueba hasta 4 endpoints de sync en orden
  - Los errores de sync se loguean como Warning pero NO se propagan
    (el CRUD ya fue exitoso y se devuelve al cliente independientemente)
"""
from app.clients.biotime_client import BioTimeClient
from app.core.logging import get_logger
from app.interfaces.sincronizacion.interface_sincronizacion import ISincronizacion

logger = get_logger(__name__)

# Endpoints de sync a intentar por terminal, en orden de prioridad.
# BioTime puede responder con distintos endpoints según la versión instalada.
_SYNC_ENDPOINTS = [
    "iclock/api/terminals/{id}/sync/",
    "iclock/api/terminals/{id}/sync_user/",
    "iclock/api/terminals/{id}/sync_transaction/",
    "personnel/api/terminal/{id}/sync/",
]


class ServicioSincronizacion(ISincronizacion):
    """
    Sincroniza todos los terminales biométricos registrados en BioTime.
    """

    def __init__(self, client: BioTimeClient):
        self._client = client

    async def sincronizar(self) -> None:
        logger.info("Iniciando sincronización de terminales biométricos")
        terminal_ids = await self._obtener_todos_los_ids_de_terminales()

        if not terminal_ids:
            logger.warning("No se encontraron terminales biométricos para sincronizar")
            return

        sincronizados = 0
        for terminal_id in terminal_ids:
            if await self._sincronizar_terminal(terminal_id):
                sincronizados += 1

        logger.info(
            "Sincronización completada",
            total_terminales=len(terminal_ids),
            sincronizados=sincronizados,
        )

    async def _obtener_todos_los_ids_de_terminales(self) -> list[int]:
        """Pagina iclock/api/terminals/ y devuelve todos los IDs de terminales."""
        ids: list[int] = []
        page = 1
        while True:
            try:
                response = await self._client.get(
                    "iclock/api/terminals/", params={"page": page, "page_size": 50}
                )
                data = response.get("data", [])
                ids.extend(item["id"] for item in data if "id" in item)

                if not response.get("next"):
                    break
                page += 1
            except Exception as e:
                logger.warning("Error al obtener lista de terminales", page=page, error=str(e))
                break

        return ids

    async def _sincronizar_terminal(self, terminal_id: int) -> bool:
        """
        Intenta sincronizar un terminal probando los endpoints en orden.
        Devuelve True si alguno tuvo éxito, False si todos fallaron.
        Los errores se loguean como Warning y no se propagan.
        """
        for endpoint_template in _SYNC_ENDPOINTS:
            endpoint = endpoint_template.format(id=terminal_id)
            try:
                await self._client.post(endpoint, json={})
                logger.info("Terminal sincronizado", terminal_id=terminal_id, endpoint=endpoint)
                return True
            except Exception:
                continue

        logger.warning("No se pudo sincronizar el terminal con ningún endpoint", terminal_id=terminal_id)
        return False
