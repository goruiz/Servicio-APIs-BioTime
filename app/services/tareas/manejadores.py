"""
Manejadores de instrucciones de tareas de Preciso.
Cada función recibe una TareaDto y el BioTimeClient, ejecuta la accion
correspondiente en BioTime y devuelve un CompletarTareaPayload.

Formato de respuesta para Preciso:
  "0"                        : sin datos o sin error
  "campo1|campo2&campo1|..." : datos tabulados (pipes entre campos, ampersand entre registros)

Instrucciones y servicio que utilizan:
  EMPMAR / EMPMAD : ServicioTerminales + ServicioMarcaciones
  DISDAT          : ServicioTerminales
  EMPHUE          : ServicioBiodata
  DELHUE          : ServicioBiodata
  COPHUE / REPHUE : ServicioTerminales + ServicioBiodata
  EMPDAT          : ServicioEmpleado
  EMPDEL          : ServicioEmpleado
  EMPUDT          : ServicioEmpleado
  UPDTFH / ASGPRV / ADDADM / EMPCLA : sin implementacion via REST
"""
import datetime
import json
from typing import Optional

from app.clients.biotime_client import BioTimeClient
from app.core.config import settings
from app.db.conexion import obtener_pool
from app.interfaces.sincronizacion.interface_sincronizacion import (
    ISincronizacion,
    SincronizacionDeshabilitada,
)
from app.schemas.empleado.respuesta_empleado import EmpleadoCreateUpdateDto
from app.schemas.tareas.tarea import CompletarTarea, TareaDto
from app.db.repositorios.repositorio_empmar_cursor import RepositorioEmpmarCursor
from app.db.repositorios.repositorio_empleado import RepositorioEmpleado
from app.services.empleado.servicio_empleado import ServicioEmpleado
from app.services.huellas.servicio_biodata import ServicioBiodata
from app.services.marcaciones.servicio_marcaciones import ServicioMarcaciones
from app.services.sincronizacion.servicio_sincronizacion import ServicioSincronizacion
from app.services.tareas.interface_tareas import TareaPendiente
from app.services.terminales.servicio_terminales import ServicioTerminales


# Factories de servicios


# Devuelve una instancia de ServicioEmpleado para el cliente de la tarea actual
def _servicio_empleado(client: BioTimeClient) -> ServicioEmpleado:
    return ServicioEmpleado(client, RepositorioEmpleado(obtener_pool()))


# Devuelve una instancia de ServicioTerminales para el cliente de la tarea actual
def _servicio_terminales(client: BioTimeClient) -> ServicioTerminales:
    return ServicioTerminales(client)


# Devuelve una instancia de ServicioMarcaciones para el cliente de la tarea actual
def _servicio_marcaciones(client: BioTimeClient) -> ServicioMarcaciones:
    return ServicioMarcaciones(client)


# Devuelve una instancia de ServicioBiodata para el cliente de la tarea actual
def _servicio_biodata(client: BioTimeClient) -> ServicioBiodata:
    return ServicioBiodata(client, obtener_pool())


# Devuelve ServicioSincronizacion o SincronizacionDeshabilitada según la configuración
def _servicio_sincronizacion(client: BioTimeClient) -> ISincronizacion:
    if settings.BIOTIME_SYNC_HABILITADO:
        return ServicioSincronizacion(client)
    return SincronizacionDeshabilitada()


# Helpers


# Parsea el detalle de una tarea de empleado y construye el DTO con los datos de configuracion por defecto
def _parsear_datos_empleado(detalle: str, settings_) -> tuple[str, EmpleadoCreateUpdateDto]:
    partes = detalle.split("|")
    
    emp_code = partes[0]
    nombre_completo = (
        partes[1].strip()
        if len(partes) > 1 and partes[1].strip()
        else emp_code
    )
    partes_nombre = nombre_completo.split()


    if len(partes_nombre) >= 4:
        first_name = " ".join(partes_nombre[:2])
        last_name = " ".join(partes_nombre[2:])

    elif len(partes_nombre) == 3:
        first_name = partes_nombre[0]
        last_name = " ".join(partes_nombre[1:])

    elif len(partes_nombre) == 2:
        first_name = partes_nombre[0]
        last_name = partes_nombre[1]

    else:
        first_name = nombre_completo
        last_name = ""


    first_name = first_name[:25]
    last_name = last_name[:25]
    
    card_no = partes[3] if len(partes) > 3 and partes[3].strip() else None
    device_password = partes[4] if len(partes) > 4 and partes[4].strip() else None
    department_raw = partes[5].strip() if len(partes) > 5 and partes[5].strip() else None
    area_raw = partes[6].strip() if len(partes) > 6 and partes[6].strip() else None
    department = int(department_raw) if department_raw else settings_.BIOTIME_DEFAULT_DEPARTMENT_ID
    area = [int(area_raw)] if area_raw else [settings_.BIOTIME_DEFAULT_AREA_ID]
    datos = EmpleadoCreateUpdateDto(
        emp_code=emp_code,
        first_name=first_name,
        last_name=last_name,
        company=settings_.BIOTIME_DEFAULT_COMPANY_ID,
        department=department,
        area=area,
        card_no=card_no,
        device_password=device_password,
    )
    return emp_code, datos


# Manejadores de marcaciones


# Lee las marcaciones no procesadas del terminal usando cursor persistente por terminal
async def ejecutar_empmar(tarea: TareaDto, client: BioTimeClient) -> CompletarTarea:
    print(f"[EMPMAR] Inicio — IP={tarea.ip} | emp_code={tarea.detalle}")

    terminal = await _servicio_terminales(client).buscar_por_ip(tarea.ip)
    if not terminal:
        print(f"[EMPMAR] Terminal no encontrado para IP={tarea.ip} — cerrando tarea sin marcaciones")
        return CompletarTarea(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)
    print(f"[EMPMAR] Terminal encontrado — SN={terminal.sn} | ID={terminal.id}")

    cursor = RepositorioEmpmarCursor(obtener_pool())
    ultima_punch_time = await cursor.obtener_cursor(terminal.sn)

    if ultima_punch_time:
        # +1 segundo para no repetir la última marcación ya enviada
        fecha_inicio = (
            datetime.datetime.strptime(ultima_punch_time, "%Y-%m-%d %H:%M:%S")
            + datetime.timedelta(seconds=1)
        ).strftime("%Y-%m-%d %H:%M:%S")
        print(f"[EMPMAR] Cursor encontrado — consultando desde {fecha_inicio}")
    else:
        fecha_inicio = None
        print(f"[EMPMAR] Sin cursor previo — consultando todas las marcaciones del terminal")

    marcaciones = await _servicio_marcaciones(client).obtener_marcaciones_por_terminal(terminal.sn, fecha_inicio)
    print(f"[EMPMAR] {len(marcaciones)} marcación(es) obtenida(s)")

    nueva_punch_time = max(m.punch_time for m in marcaciones) if marcaciones else None

    async def _guardar_cursor() -> None:
        await cursor.actualizar_cursor(terminal.sn, nueva_punch_time)
        print(f"[EMPMAR] Cursor actualizado → {nueva_punch_time}")

    partes = [f"{m.emp_code}|{m.punch_time}" for m in marcaciones]
    for i, p in enumerate(partes, 1):
        print(f"[EMPMAR]   [{i}] {p}")
    respuesta = "&".join(partes) if partes else "0"
    print(f"[EMPMAR] Respuesta final: {respuesta}")
    return CompletarTarea(
        id_tarea=tarea.id_tarea,
        instruccion=tarea.instruccion,
        respuesta=respuesta,
        on_completado=_guardar_cursor if nueva_punch_time else None,
    )


# Lee las marcaciones del terminal igual que EMPMAR (el borrado lo realiza el daemon directamente en el dispositivo)
async def ejecutar_empmad(tarea: TareaDto, client: BioTimeClient) -> CompletarTarea:
    payload = await ejecutar_empmar(tarea, client)
    payload.instruccion = "EMPMAD"
    return payload


# Manejadores de terminales


# Obtiene los datos del dispositivo: numero de serie, version de firmware y MAC
async def ejecutar_disdat(tarea: TareaDto, client: BioTimeClient) -> CompletarTarea:
    terminal = await _servicio_terminales(client).buscar_por_ip(tarea.ip)
    if not terminal:
        print(f"[Tareas] DISDAT — IP={tarea.ip} no encontrado en BioTime, cerrando tarea sin datos")
        return CompletarTarea(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion, id_tabla=tarea.id_tabla, respuesta="||")

    respuesta = f"{terminal.sn}|{terminal.firmware_ver or ''}|{terminal.mac or ''}"
    print(f"[Tareas] DISDAT — IP={tarea.ip} SN={terminal.sn}")
    return CompletarTarea(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion, id_tabla=tarea.id_tabla, respuesta=respuesta)


# Manejadores de huellas dactilares


# Obtiene los templates biometricos de un empleado desde BioTime
async def ejecutar_emphue(tarea: TareaDto, client: BioTimeClient) -> CompletarTarea:
    emp_code = tarea.detalle
    print(f"[EMPHUE] emp_code={emp_code}")
    templates = await _servicio_biodata(client).obtener_templates_por_emp_code(emp_code)
    if templates:
        respuesta = "&".join(json.dumps(t, separators=(",", ":")) for t in templates)
        print(f"[EMPHUE] {len(templates)} template(s) — fids={[t['fid'] for t in templates]}")
    else:
        raise TareaPendiente(f"EMPHUE emp_code={emp_code} — sin templates, tarea queda pendiente")
    return CompletarTarea(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion, respuesta=respuesta)


# Elimina todos los templates biometricos de un empleado en BioTime
async def ejecutar_delhue(tarea: TareaDto, client: BioTimeClient) -> CompletarTarea:
    emp_code = tarea.detalle
    print(f"[DELHUE] emp_code={emp_code}")
    await _servicio_biodata(client).eliminar_por_emp_code(emp_code)
    return CompletarTarea(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)


# Copia un template biometrico al terminal indicado. detalle: "emp_code|bio_data"
async def ejecutar_cophue(tarea: TareaDto, client: BioTimeClient) -> CompletarTarea:
    partes = tarea.detalle.split("|", 1)
    emp_code = partes[0]
    bio_data = partes[1] if len(partes) > 1 else ""
    if not bio_data or bio_data == "0":
        raise TareaPendiente(f"COPHUE emp_code={emp_code} — sin huella, tarea queda pendiente")
    print(f"[COPHUE] emp_code={emp_code} | IP={tarea.ip} | template=presente")
    terminal = await _servicio_terminales(client).buscar_por_ip(tarea.ip)
    sn = terminal.sn if terminal else ""
    await _servicio_biodata(client).registrar_template(emp_code, bio_data, sn)
    if terminal:
        await _servicio_sincronizacion(client).sincronizar_terminal(terminal.id)
    return CompletarTarea(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)


# Replica un template biometrico al terminal indicado. detalle: "emp_code|bio_data"
async def ejecutar_rephue(tarea: TareaDto, client: BioTimeClient) -> CompletarTarea:
    emp_code, bio_data = tarea.detalle.split("|", 1)
    print(f"[REPHUE] emp_code={emp_code} | IP={tarea.ip} | template={'presente' if bio_data and bio_data != '0' else 'vacío'}")
    if bio_data and bio_data != "0":
        terminal = await _servicio_terminales(client).buscar_por_ip(tarea.ip)
        sn = terminal.sn if terminal else ""
        await _servicio_biodata(client).registrar_template(emp_code, bio_data, sn)
        if terminal:
            await _servicio_sincronizacion(client).sincronizar_terminal(terminal.id)
    else:
        print(f"[Tareas] REPHUE — emp_code={emp_code} sin template válido, cerrando tarea")
    return CompletarTarea(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)


# Manejadores de empleados


# Crea o actualiza un empleado en BioTime segun si ya existe. detalle: "emp_code|nombre|admin|tarjeta"
async def ejecutar_empdat(tarea: TareaDto, client: BioTimeClient) -> CompletarTarea:
    emp_code, datos_entrantes = _parsear_datos_empleado(tarea.detalle, settings)
    print(f"[EMPDAT] emp_code={emp_code} | nombre={datos_entrantes.first_name} {datos_entrantes.last_name} | depto={datos_entrantes.department} | area={datos_entrantes.area}")

    service = _servicio_empleado(client)
    empleado = await service.buscar_por_emp_code(emp_code)
    
    if empleado:
        await service.actualizar_empleado(empleado_id=empleado.id, datos=datos_entrantes)
    else:
        await service.crear_empleado(datos=datos_entrantes)
    await _servicio_sincronizacion(client).sincronizar()
    return CompletarTarea(
        id_tarea=tarea.id_tarea,
        instruccion=tarea.instruccion,
        id_tabla=tarea.id_tabla,
    )


# Elimina un empleado de BioTime buscandolo por emp_code. detalle: "emp_code|nombre"
async def ejecutar_empdel(tarea: TareaDto, client: BioTimeClient) -> CompletarTarea:
    emp_code = tarea.detalle.split("|")[0]
    print(f"[EMPDEL] emp_code={emp_code}")
    service = _servicio_empleado(client)
    empleado = await service.buscar_por_emp_code(emp_code)
    if empleado:
        await service.eliminar_empleados([empleado.id])
        print(f"[Tareas] EMPDEL — emp_code={emp_code} ID BioTime={empleado.id}")
        await _servicio_sincronizacion(client).sincronizar()
    else:
        print(f"[Tareas] AVISO - EMPDEL emp_code={emp_code}: no encontrado en BioTime")
    return CompletarTarea(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)


# Actualiza los datos de un empleado en BioTime. detalle: "emp_code|nombre|admin|tarjeta"
# Reglas de merge con el estado actual en BioTime:
#   - campo con valor real  → actualizar
#   - campo ausente o "0"   → preservar el valor existente
#   - campo vacío ("")      → limpiar (enviar vacío a BioTime)
async def ejecutar_empudt(tarea: TareaDto, client: BioTimeClient, cache_empleados: Optional[dict] = None) -> CompletarTarea:
    emp_code, datos = _parsear_datos_empleado(tarea.detalle, settings)
    print(f"[EMPUDT] emp_code={emp_code} | nombre={datos.first_name} {datos.last_name}")
    service = _servicio_empleado(client)
    empleado_raw = cache_empleados.get(emp_code) if cache_empleados else None
    if empleado_raw is None:
        empleado_raw = await service.buscar_raw_por_emp_code(emp_code)
    if not empleado_raw:
        print(f"[Tareas] AVISO - EMPUDT emp_code={emp_code}: no encontrado en BioTime")
        return CompletarTarea(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)

    partes = tarea.detalle.split("|")
    card_no_raw = partes[3] if len(partes) > 3 else None

    if card_no_raw is None or card_no_raw.strip() == "0":
        datos.card_no = empleado_raw.get("card_no")
    elif card_no_raw.strip() == "":
        datos.card_no = ""

    empleado_id = empleado_raw["id"]
    await service.actualizar_empleado(empleado_id=empleado_id, datos=datos, datos_actuales=empleado_raw)
    print(f"[Tareas] EMPUDT — actualizado emp_code={emp_code} ID BioTime={empleado_id}")
    await _servicio_sincronizacion(client).sincronizar()
    return CompletarTarea(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)


# Manejadores sin implementacion via REST


# BioTime sincroniza la hora automaticamente via NTP, no se requiere accion
async def ejecutar_updtfh(tarea: TareaDto, client: BioTimeClient) -> CompletarTarea:
    return CompletarTarea(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)


# Pendiente de implementacion: asignacion de privilegios en terminal
async def ejecutar_asgprv(tarea: TareaDto, client: BioTimeClient) -> CompletarTarea:
    print(f"[Tareas] AVISO - ASGPRV pendiente de implementacion")
    return CompletarTarea(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)


# Pendiente de implementacion: agregar administrador en terminal
async def ejecutar_addadm(tarea: TareaDto, client: BioTimeClient) -> CompletarTarea:
    print(f"[Tareas] AVISO - ADDADM pendiente de implementacion")
    return CompletarTarea(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)


# Pendiente de implementacion: verificacion de PIN de empleados en terminal
async def ejecutar_empcla(tarea: TareaDto, client: BioTimeClient) -> CompletarTarea:
    print(f"[Tareas] AVISO - EMPCLA pendiente de implementacion")
    return CompletarTarea(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)


# Tabla de despacho: mapea cada instruccion de Preciso a su manejador correspondiente

_MANEJADORES = {
    "EMPMAR": ejecutar_empmar,  # Lee marcaciones del terminal de las últimas 24h y las envía a Preciso
    "EMPMAD": ejecutar_empmad,  # Igual que EMPMAR (el borrado en el terminal lo hace el daemon directamente)
    "DISDAT": ejecutar_disdat,  # Lee datos técnicos del terminal (serie, firmware, MAC) y los guarda en Preciso
    "EMPHUE": ejecutar_emphue,  # Lee templates biométricos de un empleado desde PostgreSQL de BioTime
    "DELHUE": ejecutar_delhue,  # Elimina todos los templates biométricos de un empleado en BioTime
    "COPHUE": ejecutar_cophue,  # Copia un template biométrico a un terminal específico vía BioTime
    "REPHUE": ejecutar_rephue,  # Replica un template biométrico a un terminal (igual que COPHUE)
    "EMPDAT": ejecutar_empdat,  # Crea o actualiza un empleado en BioTime
    "EMPDEL": ejecutar_empdel,  # Elimina un empleado de BioTime
    "EMPUDT": ejecutar_empudt,  # Actualiza los datos de un empleado en BioTime
    "UPDTFH": ejecutar_updtfh,  # Sincroniza fecha/hora del terminal (BioTime lo maneja vía NTP, no requiere acción)
    "ASGPRV": ejecutar_asgprv,  # Asigna/revoca privilegios de administrador en terminal (pendiente de implementar)
    "ADDADM": ejecutar_addadm,  # Agrega un administrador en terminal (pendiente de implementar)
    "EMPCLA": ejecutar_empcla,  # Verifica si un empleado tiene PIN configurado en el terminal (pendiente de implementar)
}


# Despacha la tarea al manejador correspondiente
async def ejecutar(tarea: TareaDto, client: BioTimeClient, cache_empleados: Optional[dict] = None) -> CompletarTarea:
    manejador = _MANEJADORES.get(tarea.instruccion)
    if not manejador:
        print(f"[Tareas] AVISO - Instruccion desconocida: {tarea.instruccion} (ID={tarea.id_tarea})")
        return CompletarTarea(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)

    if tarea.instruccion == "EMPUDT":
        return await ejecutar_empudt(tarea, client, cache_empleados=cache_empleados)

    return await manejador(tarea, client)
