"""
Interface para el servicio de procesamiento de tareas de Preciso.
"""
from abc import ABC, abstractmethod


class TareaPendiente(Exception):
    """Se lanza cuando una tarea no puede ejecutarse aún y debe permanecer pendiente en Preciso."""


class ITareas(ABC):
    """Contrato para el servicio que procesa tareas de Preciso."""

    @abstractmethod
    async def procesar_tareas(self) -> None:
        """
        Obtiene las tareas pendientes de Preciso y las ejecuta contra BioTime.
        Se llama periódicamente por el scheduler.
        """
        ...
