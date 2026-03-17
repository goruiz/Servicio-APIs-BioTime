"""
Servicio principal de procesamiento de tareas de Preciso.
Se registra en el scheduler para ejecutarse periódicamente.
"""
from datetime import datetime

from app.clients.biotime_client import BioTimeClient
from app.clients.preciso_client import PrecisoAuthenticationError, PrecisoClient, PrecisoConnectionError
from app.core.config import settings
from app.core.scheduler import scheduler
from app.services.tareas import manejadores
from app.services.tareas.interface_tareas import ITareas, TareaPendiente

_preciso_client = PrecisoClient()
_biotime_client = BioTimeClient()

_SEP_WIDTH = 60


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
        now = datetime.now().strftime("%H:%M:%S")
        print(f"\n[Tareas] {'─' * _SEP_WIDTH}")
        print(f"[Tareas] Ciclo: {now}")
        try:
            tareas = await self._preciso.obtener_tareas()
        except (PrecisoAuthenticationError, PrecisoConnectionError) as e:
            print(f"[Tareas] ERROR - No se pudo conectar a Preciso: {e}")
            return

        if not tareas:
            print(f"[Tareas] Sin tareas pendientes")
            return

        total = len(tareas)
        print(f"\n[Tareas] {total} tarea(s) pendiente(s):")
        for i, t in enumerate(tareas, 1):
            print(f"  [{i}]  ID={t.id_tarea:<8}  {t.instruccion:<8}  IP={t.ip:<16}  {t.detalle!r}")

        for i, tarea in enumerate(tareas, 1):
            header = f"[Tareas] ── [{i}/{total}] {tarea.instruccion} #{tarea.id_tarea} "
            print(f"\n{header}{'─' * max(0, _SEP_WIDTH - len(header))}")
            try:
                payload = await manejadores.ejecutar(tarea, self._biotime)
                respuesta = await self._preciso.completar_tarea(payload)
                error_code = respuesta.get("error_code") if respuesta else None
                if error_code:
                    detalle = respuesta.get("detalle", "sin detalle")
                    print(f"[Tareas] Completado | Preciso: {detalle}")
                else:
                    print(f"[Tareas] Completado | Preciso: OK")
            except TareaPendiente as e:
                print(f"[Tareas] PENDIENTE - {e}")
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
