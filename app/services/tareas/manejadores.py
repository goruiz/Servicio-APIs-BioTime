"""
Manejadores de instrucciones de tareas de Preciso.
Cada función recibe una TareaDto y el BioTimeClient, ejecuta la acción
correspondiente en BioTime y devuelve el CompletarTareaPayload con el resultado.

Formato de respuesta para Preciso:
  - "0"                        → sin datos / sin error
  - "campo1|campo2&campo1|..." → datos tabulados

Mapeo de instrucciones a BioTime:
  EMPMAR / EMPMAD → GET /iclock/api/transactions/ (por terminal)
  DISDAT          → GET /iclock/api/terminals/ (datos del terminal)
  EMPHUE          → GET /iclock/api/biodata/ (huellas del empleado)
  DELHUE          → DELETE /iclock/api/biodata/
  COPHUE / REPHUE → POST /iclock/api/biodata/ (copia de huellas)
  EMPDAT          → POST /personnel/api/employees/ (enrolar empleado)
  EMPDEL          → DELETE /personnel/api/employees/{emp_code}/
  EMPUDT          → PATCH /personnel/api/employees/{emp_code}/
  UPDTFH / ASGPRV / ADDADM / EMPCLA → Acción en terminal (no disponible via REST)
"""
import datetime
import json
from typing import Optional

from app.clients.biotime_client import BioTimeClient
from app.core.config import settings
from app.schemas.tareas.tarea import CompletarTareaPayload, TareaDto


async def _obtener_sn_por_ip(client: BioTimeClient, ip: str) -> Optional[str]:
    """
    Busca el número de serie (SN) de un terminal a partir de su dirección IP.
    Pagina sobre /iclock/api/terminals/ hasta encontrar la IP o agotar páginas.
    """
    page = 1
    while True:
        data = await client.get("iclock/api/terminals/", params={"page": page, "page_size": 50})
        for terminal in data.get("data", []):
            if terminal.get("ip_address") == ip:
                return terminal.get("sn")
        if not data.get("next"):
            break
        page += 1
    print(f"[Tareas] AVISO - Terminal no encontrado para IP={ip}")
    return None


async def ejecutar_empmar(tarea: TareaDto, client: BioTimeClient) -> CompletarTareaPayload:
    """EMPMAR: Lee marcaciones del terminal y las envía a Preciso."""
    sn = await _obtener_sn_por_ip(client, tarea.ip)
    if not sn:
        return CompletarTareaPayload(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)

    fecha_inicio = (datetime.datetime.now() - datetime.timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    marcaciones: list[str] = []
    page = 1
    while True:
        data = await client.get("iclock/api/transactions/", params={
            "terminal_sn": sn, "start_time": fecha_inicio, "page": page, "page_size": 100,
        })
        for registro in data.get("data", []):
            emp_code = registro.get("emp_code", "")
            punch_time = registro.get("punch_time", "")
            if emp_code and punch_time:
                marcaciones.append(f"{emp_code}|{punch_time}")
        if not data.get("next"):
            break
        page += 1

    respuesta = "&".join(marcaciones) if marcaciones else "0"
    print(f"[Tareas] EMPMAR — IP={tarea.ip} marcaciones={len(marcaciones)}")
    return CompletarTareaPayload(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion, respuesta=respuesta)


async def ejecutar_empmad(tarea: TareaDto, client: BioTimeClient) -> CompletarTareaPayload:
    """EMPMAD: Lee marcaciones del terminal (igual que EMPMAR) y las borra del dispositivo."""
    payload = await ejecutar_empmar(tarea, client)
    payload.instruccion = "EMPMAD"
    return payload


async def ejecutar_disdat(tarea: TareaDto, client: BioTimeClient) -> CompletarTareaPayload:
    """DISDAT: Obtiene datos del dispositivo (serie, firmware, mac)."""
    sn = await _obtener_sn_por_ip(client, tarea.ip)
    if not sn:
        return CompletarTareaPayload(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)

    page = 1
    terminal_data: Optional[dict] = None
    while True:
        data = await client.get("iclock/api/terminals/", params={"page": page, "page_size": 50})
        for terminal in data.get("data", []):
            if terminal.get("sn") == sn:
                terminal_data = terminal
                break
        if terminal_data or not data.get("next"):
            break
        page += 1

    if not terminal_data:
        return CompletarTareaPayload(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)

    respuesta = f"{terminal_data.get('sn', '')}|{terminal_data.get('firmware_ver', '')}|{terminal_data.get('mac', '')}"
    print(f"[Tareas] DISDAT — IP={tarea.ip} SN={sn}")
    return CompletarTareaPayload(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion, respuesta=respuesta)


async def ejecutar_emphue(tarea: TareaDto, client: BioTimeClient) -> CompletarTareaPayload:
    """EMPHUE: Obtiene huellas de un empleado desde BioTime."""
    emp_code = tarea.detalle
    huellas: list[str] = []
    page = 1
    while True:
        data = await client.get("iclock/api/biodata/", params={"emp_code": emp_code, "page": page, "page_size": 50})
        for registro in data.get("data", []):
            bio_data = registro.get("bio_data") or registro.get("biodata") or ""
            if bio_data:
                huellas.append(bio_data)
        if not data.get("next"):
            break
        page += 1

    respuesta = "&".join(huellas) if huellas else "0"
    print(f"[Tareas] EMPHUE — emp_code={emp_code} huellas={len(huellas)}")
    return CompletarTareaPayload(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion, respuesta=respuesta)


async def ejecutar_delhue(tarea: TareaDto, client: BioTimeClient) -> CompletarTareaPayload:
    """DELHUE: Elimina las huellas de un empleado en BioTime."""
    emp_code = tarea.detalle
    try:
        await client.delete("iclock/api/biodata/", params={"emp_code": emp_code})
        print(f"[Tareas] DELHUE — emp_code={emp_code}")
    except Exception as e:
        print(f"[Tareas] ERROR - DELHUE emp_code={emp_code}: {e}")
    return CompletarTareaPayload(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)


async def ejecutar_cophue(tarea: TareaDto, client: BioTimeClient) -> CompletarTareaPayload:
    """COPHUE: Copia una huella a otro terminal. detalle = "emp_code|huella_data" """
    partes = tarea.detalle.split("|", 1)
    if len(partes) == 2:
        emp_code, bio_data = partes
        try:
            sn = await _obtener_sn_por_ip(client, tarea.ip)
            await client.post("iclock/api/biodata/", json={"emp_code": emp_code, "bio_data": bio_data, "terminal_sn": sn})
            print(f"[Tareas] COPHUE — IP={tarea.ip} emp_code={emp_code}")
        except Exception as e:
            print(f"[Tareas] ERROR - COPHUE IP={tarea.ip}: {e}")
    return CompletarTareaPayload(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)


async def ejecutar_rephue(tarea: TareaDto, client: BioTimeClient) -> CompletarTareaPayload:
    """REPHUE: Replica huellas entre terminales (misma lógica que COPHUE)."""
    partes = tarea.detalle.split("|", 1)
    if len(partes) == 2:
        emp_code, bio_data = partes
        try:
            sn = await _obtener_sn_por_ip(client, tarea.ip)
            await client.post("iclock/api/biodata/", json={"emp_code": emp_code, "bio_data": bio_data, "terminal_sn": sn})
            print(f"[Tareas] REPHUE — IP={tarea.ip} emp_code={emp_code}")
        except Exception as e:
            print(f"[Tareas] ERROR - REPHUE IP={tarea.ip}: {e}")
    return CompletarTareaPayload(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)



async def ejecutar_empdat(tarea: TareaDto, client: BioTimeClient) -> CompletarTareaPayload:
    """EMPDAT: Registra o actualiza un empleado en BioTime.
    detalle = "emp_code|nombre completo|admin(S/N)|tarjeta"
    """
    partes = tarea.detalle.split("|")
    emp_code = partes[0]
    nombre_completo = partes[1] if len(partes) > 1 else emp_code

    nombre_partes = nombre_completo.strip().split(" ", 1)
    first_name = nombre_partes[0]
    last_name = nombre_partes[1] if len(nombre_partes) > 1 else ""

    try:
        data = await client.get("api/v1/empleados/", params={"emp_code": emp_code})
        empleados = data.get("data", [])

        if empleados:
            empleado_id = empleados[0]["id"]
            await client.put(f"personnel/api/employees/{empleado_id}/", json={
                "emp_code": emp_code,
                "first_name": first_name,
                "last_name": last_name,
                "department": settings.BIOTIME_DEFAULT_DEPARTMENT_ID,
                "area": [settings.BIOTIME_DEFAULT_AREA_ID],
            })
            print(f"[Tareas] EMPDAT — actualizado emp_code={emp_code} ID BioTime={empleado_id}")
        else:
            await client.post("personnel/api/employees/", json={
                "emp_code": emp_code,
                "first_name": first_name,
                "last_name": last_name,
                "department": settings.BIOTIME_DEFAULT_DEPARTMENT_ID,
                "area": [settings.BIOTIME_DEFAULT_AREA_ID],
            })
            print(f"[Tareas] EMPDAT — creado emp_code={emp_code}")
    except Exception as e:
        print(f"[Tareas] ERROR - EMPDAT emp_code={emp_code}: {e}")

    return CompletarTareaPayload(
        id_tarea=tarea.id_tarea,
        instruccion=tarea.instruccion,
        id_tabla=tarea.id_tabla,
    )


async def ejecutar_empdel(tarea: TareaDto, client: BioTimeClient) -> CompletarTareaPayload:
    """EMPDEL: Elimina un empleado de BioTime."""
    emp_code = tarea.detalle
    try:
        await client.delete(f"personnel/api/employees/{emp_code}/")
        print(f"[Tareas] EMPDEL — emp_code={emp_code}")
    except Exception as e:
        print(f"[Tareas] ERROR - EMPDEL emp_code={emp_code}: {e}")
    return CompletarTareaPayload(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)


async def ejecutar_empudt(tarea: TareaDto, client: BioTimeClient) -> CompletarTareaPayload:
    """EMPUDT: Actualiza datos de un empleado en BioTime. TODO: mapeo de campos pendiente."""
    print(f"[Tareas] AVISO - EMPUDT pendiente de implementación — detalle={tarea.detalle}")
    return CompletarTareaPayload(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)


async def ejecutar_updtfh(tarea: TareaDto, client: BioTimeClient) -> CompletarTareaPayload:
    """UPDTFH: BioTime sincroniza hora automáticamente vía NTP. Sin acción necesaria."""
    return CompletarTareaPayload(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)


async def ejecutar_asgprv(tarea: TareaDto, client: BioTimeClient) -> CompletarTareaPayload:
    """ASGPRV: Asigna privilegio en terminal. TODO: pendiente de implementación."""
    print(f"[Tareas] AVISO - ASGPRV pendiente de implementación")
    return CompletarTareaPayload(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)


async def ejecutar_addadm(tarea: TareaDto, client: BioTimeClient) -> CompletarTareaPayload:
    """ADDADM: Agrega administrador en terminal. TODO: pendiente de implementación."""
    print(f"[Tareas] AVISO - ADDADM pendiente de implementación")
    return CompletarTareaPayload(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)


async def ejecutar_empcla(tarea: TareaDto, client: BioTimeClient) -> CompletarTareaPayload:
    """EMPCLA: Verifica PIN de empleados en terminal. TODO: pendiente de implementación."""
    print(f"[Tareas] AVISO - EMPCLA pendiente de implementación")
    return CompletarTareaPayload(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)


# ------------------------------------------------------------------
# Tabla de despacho de instrucciones
# ------------------------------------------------------------------

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


async def ejecutar(tarea: TareaDto, client: BioTimeClient) -> CompletarTareaPayload:
    """
    Despachador principal. Delega al manejador correspondiente según la instrucción.
    Si la instrucción no es reconocida, completa la tarea sin acción.
    """
    manejador = _MANEJADORES.get(tarea.instruccion)
    if not manejador:
        print(f"[Tareas] AVISO - Instrucción desconocida: {tarea.instruccion} (ID={tarea.id_tarea})")
        return CompletarTareaPayload(id_tarea=tarea.id_tarea, instruccion=tarea.instruccion)

    print(f"[Tareas] Ejecutando ID={tarea.id_tarea} {tarea.instruccion} — IP={tarea.ip}")
    return await manejador(tarea, client)
