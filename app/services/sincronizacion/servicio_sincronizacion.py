"""
Servicio de sincronización de terminales biométricos.
Replica la lógica del proyecto C# de referencia:
  - Pagina todos los terminales desde iclock/api/terminals/
  - Por cada terminal prueba hasta 4 endpoints de sync en orden
  - Los errores de sync se loguean como Warning pero NO se propagan
    (el CRUD ya fue exitoso y se devuelve al cliente independientemente)
"""
from app.clients.biotime_client import BioTimeClient
from app.interfaces.sincronizacion.interface_sincronizacion import ISincronizacion

# Endpoints de sync a intentar por terminal, en orden de prioridad.
# BioTime puede responder con distintos endpoints según la versión instalada.
_SYNC_ENDPOINTS = [
    "iclock/api/terminals/{id}/sync/",
    "iclock/api/terminals/{id}/sync_user/",
    "iclock/api/terminals/{id}/sync_transaction/",
    "personnel/api/terminal/{id}/sync/",
]


class ServicioSincronizacion(ISincronizacion):
    """Sincroniza todos los terminales biométricos registrados en BioTime."""

    def __init__(self, client: BioTimeClient):
        self._client = client

    async def sincronizar(self) -> None:
        terminal_ids = await self._obtener_todos_los_ids_de_terminales()

        if not terminal_ids:
            print("[Sync] AVISO - Sin terminales para sincronizar")
            return

        sincronizados = 0
        for tid in terminal_ids:
            if await self._sincronizar_terminal(tid):
                sincronizados += 1

        print(f"[Sync] {sincronizados}/{len(terminal_ids)} terminal(es) sincronizados")

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
                print(f"[Sync] ERROR - Al obtener terminales: {e}")
                break
        return ids

    async def sincronizar_terminal(self, terminal_id: int) -> bool:
        return await self._sincronizar_terminal(terminal_id)

    async def _sincronizar_terminal(self, terminal_id: int) -> bool:
        """
        Intenta sincronizar un terminal probando los endpoints en orden.
        Devuelve True si alguno tuvo éxito, False si todos fallaron.
        """
        for endpoint_template in _SYNC_ENDPOINTS:
            endpoint = endpoint_template.format(id=terminal_id)
            try:
                await self._client.post(endpoint, json={})
                print(f"[Sync] Terminal ID={terminal_id} — OK via {endpoint}")
                return True
            except Exception as e:
                print(f"[Sync] Terminal ID={terminal_id} — FAIL {endpoint}: {e}")
                continue
        return False
