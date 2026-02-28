"""
Servicio de terminales biométricos.
Obtiene los datos desde la API REST de BioTime (iclock/api/terminals/).
"""
from typing import Optional

from app.clients.biotime_client import BioTimeClient
from app.core.exceptions import BioTimeException
from app.interfaces.terminales.interface_terminales import ITerminales
from app.schemas.biotime.common import PaginatedResponse
from app.schemas.terminales.respuesta_terminales import TerminalDto


class ServicioTerminales(ITerminales):

    def __init__(self, client: BioTimeClient) -> None:
        self._client = client

    async def obtener_terminales(self, page: int = 1, page_size: int = 10) -> PaginatedResponse[TerminalDto]:
        params = {"page": page, "page_size": page_size}
        response_data = await self._client.get("iclock/api/terminals/", params=params)
        terminales = [TerminalDto(**t) for t in response_data.get("data", [])]
        print(f"[Terminal] Obtenidos {len(terminales)}/{response_data.get('count', 0)} — página {page}")
        return PaginatedResponse[TerminalDto](
            count=response_data.get("count", 0),
            next=response_data.get("next"),
            previous=response_data.get("previous"),
            data=terminales,
        )

    async def obtener_terminal_por_id(self, terminal_id: int) -> TerminalDto:
        response_data = await self._client.get(f"iclock/api/terminals/{terminal_id}/")
        terminal = TerminalDto(**response_data)
        print(f"[Terminal] Obtenido — ID={terminal_id} SN={terminal.sn}")
        return terminal

    async def obtener_terminal_por_sn(self, sn: str) -> TerminalDto:
        response_data = await self._client.get("iclock/api/terminals/", params={"sn": sn})
        data = response_data.get("data", [])
        if not data:
            raise BioTimeException(status_code=404, message=f"Terminal con SN '{sn}' no encontrado")
        terminal = TerminalDto(**data[0])
        print(f"[Terminal] Obtenido — SN={sn} ID={terminal.id}")
        return terminal

    async def buscar_por_ip(self, ip: str) -> Optional[TerminalDto]:
        page = 1
        while True:
            response_data = await self._client.get("iclock/api/terminals/", params={"page": page, "page_size": 50})
            for t in response_data.get("data", []):
                if t.get("ip_address") == ip:
                    return TerminalDto(**t)
            if not response_data.get("next"):
                break
            page += 1
        print(f"[Terminal] AVISO - Terminal no encontrado para IP={ip}")
        return None
