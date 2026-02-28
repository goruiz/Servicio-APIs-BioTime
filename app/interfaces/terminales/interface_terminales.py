"""
Interfaz del servicio de terminales biométricos.
"""
from abc import ABC, abstractmethod
from typing import Optional

from app.schemas.biotime.common import PaginatedResponse
from app.schemas.terminales.respuesta_terminales import TerminalDto


class ITerminales(ABC):

    @abstractmethod
    async def obtener_terminales(
        self, page: int = 1, page_size: int = 10
    ) -> PaginatedResponse[TerminalDto]:
        """Obtiene la lista paginada de terminales registrados en BioTime."""
        pass

    @abstractmethod
    async def obtener_terminal_por_id(self, terminal_id: int) -> TerminalDto:
        """Obtiene un terminal por su ID interno de BioTime."""
        pass

    @abstractmethod
    async def obtener_terminal_por_sn(self, sn: str) -> TerminalDto:
        """Obtiene un terminal por su número de serie (SN)."""
        pass

    @abstractmethod
    async def buscar_por_ip(self, ip: str) -> Optional[TerminalDto]:
        """Busca un terminal por su dirección IP. Devuelve None si no existe."""
        pass
