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


def _filtrar_tareas_por_ip(tareas):
    """
    Aplica los filtros de IP configurados en TAREAS_IPS_PERMITIR y TAREAS_IPS_IGNORAR.
    - TAREAS_IPS_PERMITIR: si no está vacío, solo pasan las tareas cuya IP esté en la lista.
    - TAREAS_IPS_IGNORAR: si no está vacío, se descartan las tareas cuya IP esté en la lista.
    Si ambas variables están vacías, devuelve la lista sin modificar.
    """
    ips_permitir = set(settings.TAREAS_IPS_PERMITIR)
    ips_ignorar = set(settings.TAREAS_IPS_IGNORAR)
    if ips_permitir:
        tareas = [t for t in tareas if t.ip in ips_permitir]
    if ips_ignorar:
        tareas = [t for t in tareas if t.ip not in ips_ignorar]
    return tareas


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

        tareas = _filtrar_tareas_por_ip(tareas)

        if not tareas:
            print(f"[Tareas] Sin tareas pendientes tras filtro de IPs")
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

if settings.TAREAS_IPS_PERMITIR:
    print(f"[Tareas] Filtro IPs permitidas: {', '.join(settings.TAREAS_IPS_PERMITIR)}")
else:
    print(f"[Tareas] No existen IPs para filtro de permitidas")
if settings.TAREAS_IPS_IGNORAR:
    print(f"[Tareas] Filtro IPs ignoradas:  {', '.join(settings.TAREAS_IPS_IGNORAR)}")
else:
    print(f"[Tareas] No existen IPs para filtro de ignoradas")


@scheduler.registrar(
    nombre="polling_tareas_preciso",
    intervalo_segundos=settings.TAREAS_INTERVALO_SEGUNDOS,
)
async def _tarea_polling() -> None:
    """Función registrada en el scheduler. Se ejecuta cada TAREAS_INTERVALO_SEGUNDOS."""
    await _servicio.procesar_tareas()
