"""
Servicio principal de procesamiento de tareas de Preciso.
Se registra en el scheduler para ejecutarse periódicamente.
"""
import time
from datetime import datetime

from app.clients.biotime_client import BioTimeClient
from app.clients.preciso_client import (
    PrecisoAuthenticationError,
    PrecisoClient,
    PrecisoConnectionError,
)
from app.core.config import settings
from app.core.notificaciones import notificar
from app.core.scheduler import scheduler
from app.services.tareas import manejadores
from app.services.tareas.interface_tareas import ITareas, TareaPendiente
from app.services.empleado.servicio_empleado import ServicioEmpleado

_preciso_client = PrecisoClient()
_biotime_client = BioTimeClient()

TAMANO_SEPARADOR = 25


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

    def __init__(
        self,
        preciso_client: PrecisoClient,
        biotime_client: BioTimeClient,
    ) -> None:
        self._preciso = preciso_client
        self._biotime = biotime_client
        self._error_preciso_activo = False  # True mientras Preciso no responde
        # Tareas que vienen fallando con el mismo error, indexadas por "instruccion:detalle".
        # Mientras no pase TAREAS_NOTIFICACION_COOLDOWN_SEGUNDOS desde el último intento,
        # la tarea se omite: no se vuelve a ejecutar contra BioTime ni se re-notifica por
        # Telegram. Preciso sigue reencolándola en cada ciclo (no se pierde) y se reintenta
        # sola al cumplirse el plazo — si para entonces el problema ya se corrigió, se completa.
        self._tareas_en_espera: dict[str, float] = {}

    async def procesar_tareas(self) -> None:
        """
        Ciclo completo de procesamiento:
        1. Obtiene tareas pendientes de Preciso
        2. Ejecuta cada tarea contra BioTime
        3. Reporta el resultado a Preciso
        """
        now = datetime.now().strftime("%H:%M:%S")

        print(f"\n{'─' * TAMANO_SEPARADOR}[Tareas] {'─' * TAMANO_SEPARADOR}")

        try:
            tareas = await self._preciso.obtener_tareas()
            if self._error_preciso_activo:
                self._error_preciso_activo = False
                await notificar("Conexion con Preciso restaurada")
        except (PrecisoAuthenticationError, PrecisoConnectionError) as e:
            print(f"[Tareas] ERROR - No se pudo conectar a Preciso: {e}")
            if not self._error_preciso_activo:
                self._error_preciso_activo = True
                await notificar(
                    "Sin conexion con Preciso",
                    f"{type(e).__name__}: {e}",
                )
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
            print(
                f"  [{i}]  ID={t.id_tarea:<8}  {t.instruccion:<8}  "
                f"IP={t.ip:<16}  {t.detalle!r}"
            )

        if settings.UNICAMENTE_LEER_TAREAS:
            print("[Tareas] Modo solo lectura — tareas no ejecutadas (UNICAMENTE_LEER_TAREAS=True)")
            return

        # Pre-cargar datos de empleados para todas las tareas EMPUDT del lote
        cache_empleados = {}
        emp_codes_empudt = {
            t.detalle.split("|")[0]
            for t in tareas
            if t.instruccion == "EMPUDT"
        }
        if emp_codes_empudt:
            service = ServicioEmpleado(self._biotime)
            try:
                for emp_code in emp_codes_empudt:
                    raw = await service.buscar_raw_por_emp_code(emp_code)
                    if raw:
                        cache_empleados[emp_code] = raw
            except Exception as e:
                # El precache es solo una optimización: si BioTime falla acá,
                # cada EMPUDT hace su propio fetch individual (ver ejecutar_empudt),
                # ya cubierto por el manejo de errores por-tarea más abajo.
                print(f"[Tareas] AVISO - Precache de empleados falló, se continúa sin cache: {e}")

        # Frases en lenguaje claro (sin jerga técnica) de los empleados que no se
        # pudieron crear/actualizar en este ciclo, para el resumen final al usuario.
        resumenes_fallos: list[str] = []

        for i, tarea in enumerate(tareas, 1):
            header = (
                f"[Tareas] ── [{i}/{total}] "
                f"{tarea.instruccion} #{tarea.id_tarea} "
            )

            print(
                f"\n{header}"
                f"{'─' * max(0, TAMANO_SEPARADOR - len(header))}"
            )

            clave_tarea = f"{tarea.instruccion}:{tarea.detalle}"
            cooldown = settings.TAREAS_NOTIFICACION_COOLDOWN_SEGUNDOS

            ultimo_intento = self._tareas_en_espera.get(clave_tarea)
            if ultimo_intento is not None:
                transcurrido = time.monotonic() - ultimo_intento
                if transcurrido < cooldown:
                    restante_seg = int(cooldown - transcurrido)
                    restante_min = -(-restante_seg // 60)  # redondeo hacia arriba
                    print(
                        f"[Tareas] EN ESPERA - Tarea ID={tarea.id_tarea} "
                        f"({tarea.instruccion}) sigue con el mismo error; "
                        f"se reintentará en {restante_min} min (sigue pendiente en Preciso)"
                    )
                    continue

            try:
                payload = await manejadores.ejecutar(
                    tarea,
                    self._biotime,
                    cache_empleados=cache_empleados,
                )

                respuesta = await self._preciso.completar_tarea(payload)
                error_code = (
                    respuesta.get("zerror_code") if respuesta else None
                )

                if payload.on_completado:
                    await payload.on_completado()

                if error_code:
                    detalle = respuesta.get("detalle", "sin detalle")
                    print(f"[Tareas] Completado | Preciso: {detalle}")
                else:
                    print(f"[Tareas] Completado | Preciso: OK")

                # Éxito: si esta misma tarea había estado fallando, se libera de la espera
                self._tareas_en_espera.pop(clave_tarea, None)

            except TareaPendiente as e:
                print(f"[Tareas] PENDIENTE - {e}")

            except (PrecisoAuthenticationError, PrecisoConnectionError) as e:
                print(
                    f"[Tareas] ERROR - No se pudo completar tarea "
                    f"ID={tarea.id_tarea}: {e}"
                )

            except Exception as e:
                print(
                    f"[Tareas] ERROR - Tarea ID={tarea.id_tarea} "
                    f"({tarea.instruccion}): {e}"
                )
                resumen_usuario = getattr(e, "resumen_usuario", None)
                if resumen_usuario:
                    resumenes_fallos.append(resumen_usuario)

                # Marca la tarea en espera: recién llegados a este punto significa que
                # o es la primera falla, o ya pasó el cooldown y se reintentó — en
                # ambos casos corresponde (re)iniciar el plazo de espera y notificar.
                self._tareas_en_espera[clave_tarea] = time.monotonic()

                if settings.ENVIA_NOTIFICACIONES_TELEGRAM == True:
                    await notificar(
                        f"Error en tarea {tarea.instruccion} #{tarea.id_tarea}",
                        f"IP: {tarea.ip}\nDetalle: {tarea.detalle}\n\n{type(e).__name__}: {e}",
                    )

        if resumenes_fallos and settings.ENVIA_NOTIFICACIONES_TELEGRAM == True:
            cuerpo = "\n\n".join(f"• {r}" for r in resumenes_fallos)
            await notificar(
                f"{len(resumenes_fallos)} empleado(s) no se pudieron actualizar en este ciclo",
                cuerpo,
            )

# ------------------------------------------------------------------
# Registro en el scheduler global
# ------------------------------------------------------------------

_servicio = ServicioTareas(_preciso_client, _biotime_client)

if settings.TAREAS_IPS_PERMITIR:
    print(
        f"[Tareas] Filtro IPs permitidas: "
        f"{', '.join(settings.TAREAS_IPS_PERMITIR)}"
    )
else:
    print(f"[Tareas] No existen IPs para filtro de permitidas")

if settings.TAREAS_IPS_IGNORAR:
    print(
        f"[Tareas] Filtro IPs ignoradas:  "
        f"{', '.join(settings.TAREAS_IPS_IGNORAR)}"
    )
else:
    print(f"[Tareas] No existen IPs para filtro de ignoradas")


@scheduler.registrar(
    nombre="polling_tareas_preciso",
    intervalo_segundos=settings.TAREAS_INTERVALO_SEGUNDOS,
)
async def _procesar_cola_de_tareas() -> None:
    """Función registrada en el scheduler. Se ejecuta cada TAREAS_INTERVALO_SEGUNDOS."""
    await _servicio.procesar_tareas()