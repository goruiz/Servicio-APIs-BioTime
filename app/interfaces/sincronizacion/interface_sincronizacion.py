"""
Interfaz del servicio de sincronización de terminales biométricos.
"""
from abc import ABC, abstractmethod


class ISincronizacion(ABC):
    """Contrato para sincronizar los terminales biométricos contra BioTime."""

    @abstractmethod
    async def sincronizar(self) -> None:
        """
        Dispara la sincronización de todos los terminales biométricos.

        Raises:
            BioTimeAuthenticationError: Si hay error de autenticación.
            BioTimeConnectionError: Si hay error de conexión con BioTime.
        """
        pass


class SincronizacionDeshabilitada(ISincronizacion):
    """
    Null Object: implementación vacía usada cuando la sincronización está deshabilitada
    (BIOTIME_SYNC_HABILITADO=False). No realiza ninguna operación.
    """

    async def sincronizar(self) -> None:
        pass
