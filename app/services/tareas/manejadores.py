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

from app.clients.biotime_client import BioTimeClient
from app.core.config import settings
from app.schemas.empleado.respuesta_empleado import EmpleadoCreateUpdateDto
from app.schemas.tareas.tarea import CompletarTarea, TareaDto
from app.services.empleado.servicio_empleado import ServicioEmpleado
from app.services.huellas.servicio_biodata import ServicioBiodata
from app.services.marcaciones.servicio_marcaciones import ServicioMarcaciones
from app.services.terminales.servicio_terminales import ServicioTerminales


# Factories de servicios


# Devuelve una instancia de ServicioEmpleado para el cliente de la tarea actual
def _servicio_empleado(client: BioTimeClient) -> ServicioEmpleado:
    return ServicioEmpleado(client)


# Devuelve una instancia de ServicioTerminales para el cliente de la tarea actual
def _servicio_terminales(client: BioTimeClient) -> ServicioTerminales:
    return ServicioTerminales(client)


# Devuelve una instancia de ServicioMarcaciones para el cliente de la tarea actual
def _servicio_marcaciones(client: BioTimeClient) -> ServicioMarcaciones:
    return ServicioMarcaciones(client)


# Devuelve una instancia de ServicioBiodata para el cliente de la tarea actual
def _servicio_biodata(client: BioTimeClient) -> ServicioBiodata:
    return ServicioBiodata(client)


# Helpers


# Imprime en consola el resultado final de una tarea: exito o error con su mensaje
def _log_resultado(tarea: TareaDto, ok: bool, error: Exception = None) -> None:
    if ok:
        print(f"[Tareas] OK  - ID={tarea.id_tarea} {tarea.instruccion} completado")
    else:
        print(f"[Tareas] ERR - ID={tarea.id_tarea} {tarea.instruccion} fallido: {error}")


# Parsea el detalle de una tarea de empleado y construye el DTO con los datos de configuracion por defecto
def _parsear_datos_empleado(detalle: str, settings_) -> tuple[str, EmpleadoCreateUpdateDto]:
    partes = detalle.split("|")
    emp_code = partes[0]
    nombre_completo = partes[1] if len(partes) > 1 else emp_code
    nombre_partes = nombre_completo.strip().split(" ", 1)
    first_name = nombre_partes[0]
    last_name = nombre_partes[1] if len(nombre_partes) > 1 else ""
    datos = EmpleadoCreateUpdateDto(
        emp_code=emp_code,
        first_name=first_name,
        last_name=last_name,
        department=settings_.BIOTIME_DEFAULT_DEPARTMENT_ID,
        area=[settings_.BIOTIME_DEFAULT_AREA_ID],
    )
    return emp_code, datos


# Manejadores de marcaciones


# Lee las marcaciones del terminal de las ultimas 24h y las envia a Preciso
async def ejecutar_empmar(tarea: TareaDto, client: BioTimeClient) -> CompletarTarea:
    terminal = await _servicio_terminales(client).buscar_por_ip(tarea.ip)
    if not terminal:
        return CompletarTarea(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)

    fecha_inicio = (datetime.datetime.now() - datetime.timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    marcaciones = await _servicio_marcaciones(client).obtener_marcaciones_por_terminal(terminal.sn, fecha_inicio)

    partes = [f"{m.emp_code}|{m.punch_time}" for m in marcaciones]
    respuesta = "&".join(partes) if partes else "0"
    print(f"[Tareas] EMPMAR — IP={tarea.ip} marcaciones={len(marcaciones)}")
    return CompletarTarea(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion, respuesta=respuesta)


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
        return CompletarTarea(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)

    respuesta = f"{terminal.sn}|{terminal.firmware_ver or ''}|{terminal.mac or ''}"
    print(f"[Tareas] DISDAT — IP={tarea.ip} SN={terminal.sn}")
    return CompletarTarea(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion, respuesta=respuesta)


# Manejadores de huellas dactilares


# Obtiene los templates biometricos de un empleado desde BioTime
async def ejecutar_emphue(tarea: TareaDto, client: BioTimeClient) -> CompletarTarea:
    emp_code = tarea.detalle
    templates = await _servicio_biodata(client).obtener_templates_por_emp_code(emp_code)
    respuesta = "&".join(templates) if templates else "0"
    print(f"[Tareas] EMPHUE — emp_code={emp_code} huellas={len(templates)}")
    return CompletarTarea(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion, respuesta=respuesta)


# Elimina todos los templates biometricos de un empleado en BioTime
async def ejecutar_delhue(tarea: TareaDto, client: BioTimeClient) -> CompletarTarea:
    emp_code = tarea.detalle
    await _servicio_biodata(client).eliminar_por_emp_code(emp_code)
    return CompletarTarea(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)


# Copia un template biometrico al terminal indicado. detalle: "emp_code|bio_data"
async def ejecutar_cophue(tarea: TareaDto, client: BioTimeClient) -> CompletarTarea:
    emp_code, bio_data = tarea.detalle.split("|", 1)
    terminal = await _servicio_terminales(client).buscar_por_ip(tarea.ip)
    sn = terminal.sn if terminal else ""
    await _servicio_biodata(client).registrar_template(emp_code, bio_data, sn)
    return CompletarTarea(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)


# Replica un template biometrico al terminal indicado. detalle: "emp_code|bio_data"
async def ejecutar_rephue(tarea: TareaDto, client: BioTimeClient) -> CompletarTarea:
    emp_code, bio_data = tarea.detalle.split("|", 1)
    terminal = await _servicio_terminales(client).buscar_por_ip(tarea.ip)
    sn = terminal.sn if terminal else ""
    await _servicio_biodata(client).registrar_template(emp_code, bio_data, sn)
    return CompletarTarea(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)


# Manejadores de empleados


# Crea o actualiza un empleado en BioTime segun si ya existe. detalle: "emp_code|nombre|admin|tarjeta"
async def ejecutar_empdat(tarea: TareaDto, client: BioTimeClient) -> CompletarTarea:
    emp_code, datos = _parsear_datos_empleado(tarea.detalle, settings)
    service = _servicio_empleado(client)
    empleado = await service.buscar_por_emp_code(emp_code)
    if empleado:
        await service.actualizar_empleado(empleado_id=empleado.id, datos=datos)
        print(f"[Tareas] EMPDAT — actualizado emp_code={emp_code} ID BioTime={empleado.id}")
    else:
        await service.crear_empleado(datos=datos)
        print(f"[Tareas] EMPDAT — creado emp_code={emp_code}")
    return CompletarTarea(
        id_tarea=tarea.id_tarea,
        instruccion=tarea.instruccion,
        id_tabla=tarea.id_tabla,
    )


# Elimina un empleado de BioTime buscandolo por emp_code. detalle: "emp_code"
async def ejecutar_empdel(tarea: TareaDto, client: BioTimeClient) -> CompletarTarea:
    emp_code = tarea.detalle
    service = _servicio_empleado(client)
    empleado = await service.buscar_por_emp_code(emp_code)
    if empleado:
        await service.eliminar_empleados([empleado.id])
        print(f"[Tareas] EMPDEL — emp_code={emp_code} ID BioTime={empleado.id}")
    else:
        print(f"[Tareas] AVISO - EMPDEL emp_code={emp_code}: no encontrado en BioTime")
    return CompletarTarea(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)


# Actualiza los datos de un empleado en BioTime. detalle: "emp_code|nombre|admin|tarjeta"
async def ejecutar_empudt(tarea: TareaDto, client: BioTimeClient) -> CompletarTarea:
    emp_code, datos = _parsear_datos_empleado(tarea.detalle, settings)
    service = _servicio_empleado(client)
    empleado = await service.buscar_por_emp_code(emp_code)
    if empleado:
        await service.actualizar_empleado(empleado_id=empleado.id, datos=datos)
        print(f"[Tareas] EMPUDT — actualizado emp_code={emp_code} ID BioTime={empleado.id}")
    else:
        print(f"[Tareas] AVISO - EMPUDT emp_code={emp_code}: no encontrado en BioTime")
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
    "EMPMAR": ejecutar_empmar,
    "EMPMAD": ejecutar_empmad,
    "DISDAT": ejecutar_disdat,
    "EMPHUE": ejecutar_emphue,
    "DELHUE": ejecutar_delhue,
    "COPHUE": ejecutar_cophue,
    "REPHUE": ejecutar_rephue,
    "EMPDAT": ejecutar_empdat,
    "EMPDEL": ejecutar_empdel,
    "EMPUDT": ejecutar_empudt,
    "UPDTFH": ejecutar_updtfh,
    "ASGPRV": ejecutar_asgprv,
    "ADDADM": ejecutar_addadm,
    "EMPCLA": ejecutar_empcla,
}


# Despacha la tarea al manejador y registra el resultado de exito o error
async def ejecutar(tarea: TareaDto, client: BioTimeClient) -> CompletarTarea:
    manejador = _MANEJADORES.get(tarea.instruccion)
    if not manejador:
        print(f"[Tareas] AVISO - Instruccion desconocida: {tarea.instruccion} (ID={tarea.id_tarea})")
        return CompletarTarea(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)

    print(f"[Tareas] Ejecutando ID={tarea.id_tarea} {tarea.instruccion} — IP={tarea.ip} | detalle={tarea.detalle!r}")
    try:
        resultado = await manejador(tarea, client)
        _log_resultado(tarea, ok=True)
        return resultado
    except Exception as e:
        _log_resultado(tarea, ok=False, error=e)
        raise
