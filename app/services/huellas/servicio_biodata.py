"""
Servicio de biodata (templates biométricos) vía API REST de BioTime.
Usado internamente por los manejadores de tareas (EMPHUE, DELHUE, COPHUE, REPHUE).
No tiene ruta HTTP propia porque la API REST de BioTime no lo expone como recurso público.

Lectura y escritura de templates (EMPHUE, COPHUE, REPHUE): usan PostgreSQL directo (iclock_biodata),
ya que el endpoint iclock/api/biodata/ no existe en todas las versiones de BioTime.
Borrado (DELHUE): usa la API REST de BioTime (DELETE iclock/api/biodata/).
"""
import asyncpg
import base64
import json

from app.clients.biotime_client import BioTimeClient
from app.core.exceptions import BioTimeException
from app.db.repositorios.repositorio_huellas import RepositorioHuellas
from app.schemas.huellas.respuesta_huellas import (
    EstadoHuellasEmpleadoResponse,
    ResultadoSincronizacionTerminal,
    SincronizarTerminalesResponse,
)
from app.services.empleado.servicio_empleado import ServicioEmpleado


class ServicioBiodata:
    """Acceso a templates biométricos: lectura vía PostgreSQL, escritura/borrado vía BioTime REST."""

    def __init__(self, client: BioTimeClient, pool: asyncpg.Pool) -> None:
        self._client = client
        self._pool = pool

    async def obtener_templates_por_emp_code(self, emp_code: str) -> list[dict]:
        """
        Devuelve los templates de un empleado como dicts estructurados:
          {'size': int, 'uid': int, 'fid': int, 'valid': int, 'template': str_hex}
        uid = emp_code numérico si es posible, si no employee_id de BioTime.
        template = bio_tmp decodificado de base64 a hexadecimal.
        """
        empleado = await ServicioEmpleado(self._client).buscar_por_emp_code(emp_code)
        if not empleado:
            print(f"[Biodata] emp_code={emp_code} no encontrado en BioTime")
            return []

        try:
            uid = int(emp_code)
        except ValueError:
            uid = empleado.id

        repositorio = RepositorioHuellas(self._pool)
        filas = await repositorio.obtener_templates_por_empleado(empleado.id)

        templates = []
        for fila in filas:
            template_bytes = base64.b64decode(fila["bio_tmp"])
            templates.append({
                "size": len(template_bytes),
                "uid": uid,
                "fid": fila["bio_index"],
                "valid": fila["valid"],
                "template": template_bytes.hex(),
            })

        print(f"[Biodata] Obtenidos {len(templates)} templates — emp_code={emp_code} uid={uid} (employee_id={empleado.id})")
        return templates

    async def copiar_a_terminales(self, emp_code: str, terminal_ips: list[str]) -> list[dict]:
        """
        Copia los templates del empleado a uno o varios terminales.
        Por cada terminal: actualiza sn en iclock_biodata al SN de ese terminal y lo sincroniza.
        Devuelve lista de {'terminal_ip': str, 'terminal_sn': str, 'templates_registrados': int}.
        """
        from app.services.sincronizacion.servicio_sincronizacion import ServicioSincronizacion
        from app.services.terminales.servicio_terminales import ServicioTerminales

        empleado = await ServicioEmpleado(self._client).buscar_por_emp_code(emp_code)
        if not empleado:
            raise ValueError(f"No se encontró el empleado emp_code={emp_code} en BioTime")

        repositorio = RepositorioHuellas(self._pool)
        templates = await repositorio.obtener_templates_completos_por_empleado(empleado.id)

        servicio_terminales = ServicioTerminales(self._client)
        servicio_sync = ServicioSincronizacion(self._client)
        resultados = []

        for ip in terminal_ips:
            terminal = await servicio_terminales.buscar_por_ip(ip)
            if not terminal:
                raise ValueError(f"No se encontró ningún terminal con IP={ip} en BioTime")

            if templates:
                for t in templates:
                    await repositorio.insertar_o_actualizar_template(
                        employee_id=t["employee_id"],
                        bio_index=t["bio_index"],
                        bio_type=t["bio_type"],
                        bio_no=t["bio_no"],
                        bio_format=t["bio_format"],
                        major_ver=t["major_ver"],
                        minor_ver=t["minor_ver"],
                        valid=t["valid"],
                        duress=t["duress"],
                        bio_tmp=t["bio_tmp"],
                        sn=terminal.sn,
                    )
                await servicio_sync.sincronizar_terminal(terminal.id)

            print(f"[Biodata] Copiados {len(templates)} template(s) — emp_code={emp_code} terminal={ip} SN={terminal.sn}")
            resultados.append({
                "terminal_ip": ip,
                "terminal_sn": terminal.sn,
                "templates_registrados": len(templates),
            })

        return resultados

    async def obtener_estado_huellas(self, emp_code: str) -> EstadoHuellasEmpleadoResponse:
        """Indica si un empleado tiene huellas y en qué terminales están registradas."""
        empleado = await ServicioEmpleado(self._client).buscar_por_emp_code(emp_code)
        if not empleado:
            raise ValueError(f"No se encontró el empleado emp_code={emp_code} en BioTime")

        repositorio = RepositorioHuellas(self._pool)
        sns = await repositorio.obtener_sns_por_empleado(empleado.id)

        print(f"[Biodata] Estado huellas — emp_code={emp_code}: {len(sns)} terminal(es)")
        return EstadoHuellasEmpleadoResponse(
            emp_code=emp_code,
            tiene_huellas=len(sns) > 0,
            terminales=sns,
        )

    async def sincronizar_entre_terminales(
        self, sn_origen: str, sns_destino: list[str]
    ) -> SincronizarTerminalesResponse:
        """Copia todas las huellas del terminal origen a uno o varios terminales destino.
        Omite huellas que ya existan en cada destino. Verifica en BD que los datos quedaron correctamente."""
        from app.services.terminales.servicio_terminales import ServicioTerminales

        repositorio = RepositorioHuellas(self._pool)
        servicio_terminales = ServicioTerminales(self._client)

        total_origen = await repositorio.contar_huellas_por_terminal(sn_origen)
        if total_origen == 0:
            raise ValueError(f"El terminal SN={sn_origen} no tiene huellas registradas")

        sns_destino_validos = [sn for sn in sns_destino if sn != sn_origen]

        resultados = []
        for sn_destino in sns_destino_validos:
            try:
                await servicio_terminales.obtener_terminal_por_sn(sn_destino)
            except BioTimeException:
                raise ValueError(f"Terminal destino SN={sn_destino} no encontrado en BioTime")

            huellas_copiadas = await repositorio.copiar_huellas_entre_terminales(sn_origen, sn_destino)
            total_destino = await repositorio.contar_huellas_por_terminal(sn_destino)
            verificado = total_destino >= total_origen

            print(
                f"[Biodata] Terminal SN={sn_destino} — "
                f"{huellas_copiadas} nuevas insertadas | "
                f"origen={total_origen} destino={total_destino} verificado={'OK' if verificado else 'INCOMPLETO'}"
            )
            resultados.append(ResultadoSincronizacionTerminal(
                sn_destino=sn_destino,
                huellas_copiadas=huellas_copiadas,
                sincronizado=verificado,
            ))

        # Encolar FINGERTMP para todos los destinos con sensor de huella (fp_count > 0)
        comandos = await repositorio.encolar_fingertmp_masivo(sns=sns_destino_validos)
        total_comandos = sum(r["comandos_encolados"] for r in comandos)
        print(f"[Biodata] FINGERTMP encolados — {total_comandos} comandos hacia {len(comandos)} terminal(es)")

        return SincronizarTerminalesResponse(
            sn_origen=sn_origen,
            total_huellas_origen=total_origen,
            terminales=resultados,
        )

    async def enviar_huellas_a_terminales(self, sns: list[str] | None = None) -> dict:
        """Encola comandos DATA UPDATE FINGERTMP para todos los templates en iclock_biodata
        de terminales con sensor de huella. BioTime los entrega al hardware en el próximo poll."""
        repositorio = RepositorioHuellas(self._pool)
        resultados = await repositorio.encolar_fingertmp_masivo(sns=sns)
        total = sum(r["comandos_encolados"] for r in resultados)
        print(f"[Biodata] Enviadas huellas a terminales — {total} comandos encolados en {len(resultados)} terminal(es)")
        return {"total_comandos": total, "terminales": resultados}

    async def eliminar_por_emp_code(self, emp_code: str) -> None:
        """Elimina todos los templates biométricos de un empleado en BioTime."""
        await self._client.delete("iclock/api/biodata/", params={"emp_code": emp_code})
        print(f"[Biodata] Eliminados templates — emp_code={emp_code}")

    async def registrar_template(self, emp_code: str, bio_data: str, terminal_sn: str) -> None:
        """Registra un template biométrico directamente en PostgreSQL (iclock_biodata).

        iclock/api/biodata/ no existe en todas las versiones de BioTime, por lo que
        se escribe en la base de datos y BioTime lo sincroniza al terminal via su propio ciclo.
        bio_data debe ser JSON: {'size': int, 'uid': int, 'fid': int, 'valid': int, 'template': str_hex}
        """
        try:
            datos = json.loads(bio_data)
            template_bytes = bytes.fromhex(datos["template"])
            bio_tmp = base64.b64encode(template_bytes).decode()
            bio_index = datos["fid"]
            valid = datos.get("valid", 1)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise ValueError(f"bio_data inválido: {e}") from e

        empleado = await ServicioEmpleado(self._client).buscar_por_emp_code(emp_code)
        if not empleado:
            raise ValueError(f"No se encontró el empleado emp_code={emp_code} en BioTime")

        repositorio = RepositorioHuellas(self._pool)
        await repositorio.insertar_o_actualizar_template(
            employee_id=empleado.id,
            bio_index=bio_index,
            bio_type=1,
            bio_no=0,
            bio_format=0,
            major_ver="10",
            minor_ver="0",
            valid=valid,
            duress=0,
            bio_tmp=bio_tmp,
            sn=terminal_sn,
        )
        print(f"[Biodata] Template registrado en PostgreSQL — emp_code={emp_code} fid={bio_index} SN={terminal_sn}")

        terminal = await repositorio.obtener_terminal_por_sn(terminal_sn)
        if terminal and terminal["finger_fun_on"]:
            await repositorio.encolar_fingertmp(
                terminal_id=terminal["id"],
                emp_code=emp_code,
                bio_index=bio_index,
                valid=valid,
                bio_tmp=bio_tmp,
            )
            print(f"[Biodata] Comando FINGERTMP encolado — terminal_id={terminal['id']} SN={terminal_sn}")
        elif terminal:
            print(f"[Biodata] Terminal SN={terminal_sn} sin FingerFunOn — FINGERTMP omitido")
