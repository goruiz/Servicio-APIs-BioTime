"""
Servicio principal de procesamiento de tareas de Preciso.
Se registra en el scheduler para ejecutarse periódicamente.
"""
from app.clients.biotime_client import BioTimeClient
from app.clients.preciso_client import PrecisoAuthenticationError, PrecisoClient, PrecisoConnectionError
from app.core.config import settings
from app.core.scheduler import scheduler
from app.services.tareas import manejadores
from app.services.tareas.interface_tareas import ITareas

_preciso_client = PrecisoClient()
_biotime_client = BioTimeClient()


class ServicioTareas(ITareas):
    """
    Implementación del servicio de tareas.
    Orquesta el ciclo: obtener → ejecutar → completar.
    """

    def __init__(self, preciso_client: PrecisoClient, biotime_client: BioTimeClient) -> None:
        self._preciso = preciso_client
        self._biotime = biotime_client

    async def procesar_tareas(self) -> None:
        """
        Ciclo completo de procesamiento:
        1. Obtiene tareas pendientes de Preciso
        2. Ejecuta cada tarea contra BioTime
        3. Reporta el resultado a Preciso
        """
        try:
            tareas = await self._preciso.obtener_tareas()
        except (PrecisoAuthenticationError, PrecisoConnectionError) as e:
            print(f"[Tareas] ERROR - No se pudo conectar a Preciso: {e}")
            return

        if not tareas:
            return  # Sin ruido cuando no hay tareas

        print(f"[Tareas] {len(tareas)} tarea(s) pendiente(s)")
        for tarea in tareas:
            try:
                payload = await manejadores.ejecutar(tarea, self._biotime)
                await self._preciso.completar_tarea(payload)
            except (PrecisoAuthenticationError, PrecisoConnectionError) as e:
                print(f"[Tareas] ERROR - No se pudo completar tarea ID={tarea.id_tarea}: {e}")
            except Exception as e:
                print(f"[Tareas] ERROR - Tarea ID={tarea.id_tarea} ({tarea.instruccion}): {e}")


# ------------------------------------------------------------------
# Registro en el scheduler global
# ------------------------------------------------------------------

_servicio = ServicioTareas(_preciso_client, _biotime_client)


@scheduler.registrar(
    nombre="polling_tareas_preciso",
    intervalo_segundos=settings.TAREAS_INTERVALO_SEGUNDOS,
)
async def _tarea_polling() -> None:
    """Función registrada en el scheduler. Se ejecuta cada TAREAS_INTERVALO_SEGUNDOS."""
    await _servicio.procesar_tareas()
