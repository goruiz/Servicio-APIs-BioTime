"""
Servicio de marcaciones.
Lógica de negocio para interactuar con el recurso de transacciones de BioTime.
"""
from typing import Optional

from app.clients.biotime_client import BioTimeClient
from app.core.exceptions import BioTimeNotFoundError
from app.interfaces.marcaciones.interface_marcaciones import IMarcaciones
from app.schemas.biotime.common import PaginatedResponse
from app.schemas.marcaciones.respuesta_marcaciones import MarcacionesDto


class ServicioMarcaciones(IMarcaciones):
    """Implementación del servicio de marcaciones."""

    def __init__(self, client: BioTimeClient):
        self._client = client

    async def obtener_marcaciones(self, page: int = 1, page_size: int = 10) -> PaginatedResponse[MarcacionesDto]:
        params = {"page": page, "page_size": page_size}
        response_data = await self._client.get("iclock/api/transactions/", params=params)
        marcaciones = [MarcacionesDto(**marc) for marc in response_data.get("data", [])]
        result = PaginatedResponse[MarcacionesDto](
            count=response_data.get("count", 0),
            next=response_data.get("next"),
            previous=response_data.get("previous"),
            data=marcaciones,
        )
        print(f"[Marcaciones] Obtenidas {len(marcaciones)}/{result.count} — página {page}")
        return result

    async def obtener_marcaciones_por_empleado(
        self,
        codigo_empleado: str,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> PaginatedResponse[MarcacionesDto]:
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
        print(f"[Marcaciones] Obtenidas {len(marcaciones)}/{result.count} — emp_code={codigo_empleado}")
        return result

    async def obtener_marcaciones_por_terminal(
        self,
        terminal_sn: str,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
        page_size: int = 100,
    ) -> list[MarcacionesDto]:
        marcaciones: list[MarcacionesDto] = []
        page = 1
        while True:
            params: dict = {"terminal_sn": terminal_sn, "page": page, "page_size": page_size}
            if fecha_inicio is not None:
                params["start_time"] = fecha_inicio
            if fecha_fin is not None:
                params["end_time"] = fecha_fin
            response_data = await self._client.get("iclock/api/transactions/", params=params)
            marcaciones.extend(MarcacionesDto(**marc) for marc in response_data.get("data", []))
            if not response_data.get("next"):
                break
            page += 1
        print(f"[Marcaciones] Obtenidas {len(marcaciones)} por terminal — SN={terminal_sn}")
        return marcaciones

    async def obtener_marcaciones_por_serial(
        self,
        terminal_sn: str,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> PaginatedResponse[MarcacionesDto]:
        params: dict = {"terminal_sn": terminal_sn, "page": page, "page_size": page_size}
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
        print(f"[Marcaciones] Obtenidas {len(marcaciones)}/{result.count} — terminal_sn={terminal_sn}")
        return result

    async def obtener_marcaciones_por_ip(
        self,
        ip_terminal: str,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> PaginatedResponse[MarcacionesDto]:
        terminal_sn = await self._buscar_sn_por_ip(ip_terminal)
        if terminal_sn is None:
            raise BioTimeNotFoundError(f"Terminal con IP '{ip_terminal}' no encontrado")
        return await self.obtener_marcaciones_por_serial(
            terminal_sn=terminal_sn,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            page=page,
            page_size=page_size,
        )

    async def _buscar_sn_por_ip(self, ip: str) -> Optional[str]:
        page = 1
        while True:
            response_data = await self._client.get("iclock/api/terminals/", params={"page": page, "page_size": 50})
            for t in response_data.get("data", []):
                if t.get("ip_address") == ip:
                    return t.get("sn")
            if not response_data.get("next"):
                break
            page += 1
        return None

    async def eliminar_marcaciones_por_id(self, id_marcacion: str) -> None:
        await self._client.delete(f"iclock/api/transactions/{id_marcacion}/")
        print(f"[Marcaciones] Eliminada — ID={id_marcacion}")

    async def eliminar_marcaciones(
        self,
        codigo_empleado: Optional[str] = None,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
    ) -> int:
        params: dict = {"page_size": 100}
        if codigo_empleado is not None:
            params["emp_code"] = codigo_empleado
        if fecha_inicio is not None:
            params["start_time"] = fecha_inicio
        if fecha_fin is not None:
            params["end_time"] = fecha_fin

        ids_a_eliminar: list[int] = []
        page = 1
        while True:
            params["page"] = page
            response_data = await self._client.get("iclock/api/transactions/", params=params)
            ids_a_eliminar.extend(item["id"] for item in response_data.get("data", []))
            if not response_data.get("next"):
                break
            page += 1

        for id_marcacion in ids_a_eliminar:
            await self._client.delete(f"iclock/api/transactions/{id_marcacion}/")

        print(f"[Marcaciones] Eliminadas {len(ids_a_eliminar)} — emp_code={codigo_empleado}")
        return len(ids_a_eliminar)
