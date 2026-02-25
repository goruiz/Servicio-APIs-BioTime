"""
Scheduler de tareas periódicas basado en asyncio nativo.
"""
import asyncio
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from typing import Any


@dataclass
class _TareaPeriodica:
    nombre: str
    intervalo_segundos: int
    funcion: Callable[[], Coroutine[Any, Any, None]]


async def _loop_periodico(tarea: _TareaPeriodica) -> None:
    """Ejecuta una función periódicamente con manejo de errores."""
    while True:
        try:
            await tarea.funcion()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"[Scheduler] ERROR en {tarea.nombre}: {e}")
        await asyncio.sleep(tarea.intervalo_segundos)


class Scheduler:
    """
    Gestor de tareas periódicas en background.

    Uso con decorador:
        @scheduler.registrar("mi_tarea", intervalo_segundos=60)
        async def mi_tarea():
            ...

    Ciclo de vida (en lifespan de FastAPI):
        scheduler.iniciar()
        yield
        scheduler.detener()
    """

    def __init__(self) -> None:
        self._tareas: list[_TareaPeriodica] = []
        self._asyncio_tasks: list[asyncio.Task] = field(default_factory=list)
        self._asyncio_tasks = []

    def registrar(self, nombre: str, intervalo_segundos: int):
        """Decorador para registrar una función como tarea periódica."""

        def decorador(func: Callable[[], Coroutine[Any, Any, None]]):
            self._tareas.append(_TareaPeriodica(nombre, intervalo_segundos, func))
            return func

        return decorador

    def iniciar(self) -> None:
        """Inicia todos los loops en background. Llamar dentro del lifespan de FastAPI."""
        for tarea in self._tareas:
            task = asyncio.create_task(_loop_periodico(tarea), name=tarea.nombre)
            self._asyncio_tasks.append(task)
        print(f"[Scheduler] {len(self._tareas)} tarea(s) activa(s)")

    def detener(self) -> None:
        """Cancela todas las tareas periódicas. Llamar al cerrar la aplicación."""
        for task in self._asyncio_tasks:
            task.cancel()
        self._asyncio_tasks.clear()


# Instancia global compartida
scheduler = Scheduler()
