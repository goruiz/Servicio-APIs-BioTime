"""
Scheduler de tareas periódicas basado en asyncio nativo.
"""
import asyncio
import time
import traceback
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from typing import Any

_INTERVALO_MINIMO_NOTIF = 15 * 60  # segundos entre notificaciones por la misma tarea


@dataclass
class _TareaPeriodica:
    nombre: str
    intervalo_segundos: int
    funcion: Callable[[], Coroutine[Any, Any, None]]
    _ultima_notif: float = field(default=0.0, init=False)


async def _loop_periodico(tarea: _TareaPeriodica) -> None:
    """
    Ejecuta una función periódicamente con manejo de errores.

    El intervalo es fijo: cada `intervalo_segundos` se verifica si la ejecución
    anterior terminó. Si aún está en curso, se omite el turno y se vuelve a
    intentar en el siguiente ciclo.
    """
    _en_ejecucion = False
    _tarea_actual: asyncio.Task | None = None

    async def _ejecutar() -> None:
        nonlocal _en_ejecucion
        _en_ejecucion = True
        try:
            await tarea.funcion()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"[Scheduler] ERROR en {tarea.nombre}: {e}")
            ahora = time.monotonic()
            if ahora - tarea._ultima_notif >= _INTERVALO_MINIMO_NOTIF:
                tarea._ultima_notif = ahora
                from app.core.notificaciones import notificar  # lazy para evitar import circular
                await notificar(
                    f"Error en tarea periodica: {tarea.nombre}",
                    f"{type(e).__name__}: {e}\n\n{traceback.format_exc(limit=8)}",
                )
        finally:
            _en_ejecucion = False

    # Primera ejecución inmediata al arrancar
    _tarea_actual = asyncio.create_task(_ejecutar(), name=f"{tarea.nombre}_run")

    while True:
        try:
            await asyncio.sleep(tarea.intervalo_segundos)
        except asyncio.CancelledError:
            if _tarea_actual and not _tarea_actual.done():
                _tarea_actual.cancel()
                try:
                    await _tarea_actual
                except (asyncio.CancelledError, Exception):
                    pass
            raise

        if _en_ejecucion:
            print(f"[Scheduler] {tarea.nombre}: ciclo anterior aún en ejecución, se omite este turno")
        else:
            _tarea_actual = asyncio.create_task(_ejecutar(), name=f"{tarea.nombre}_run")


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

    def detener(self) -> None:
        """Cancela todas las tareas periódicas. Llamar al cerrar la aplicación."""
        for task in self._asyncio_tasks:
            task.cancel()
        self._asyncio_tasks.clear()


# Instancia global compartida
scheduler = Scheduler()
