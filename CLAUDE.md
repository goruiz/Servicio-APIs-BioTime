# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Propósito

Este proyecto es un servicio middleware REST para conectarse a las APIs de **BioTime**, la aplicación de gestión de asistencia y acceso de **ZKTeco** (fabricante de dispositivos biométricos: lectores de huella dactilar, reconocimiento facial, tarjetas RFID, etc.).

BioTime centraliza los registros de marcaciones (entradas/salidas) capturados por los terminales biométricos ZKTeco y expone una API REST propia. Este middleware actúa como capa de integración: maneja autenticación JWT contra BioTime de forma automática y transparente, y expone una interfaz limpia y tipada para que otros sistemas consuman los datos sin preocuparse por los detalles del protocolo de BioTime.

Además de consumir la API REST de BioTime, el servicio se conecta **directamente a la base de datos PostgreSQL** de BioTime para acceder a datos que la API REST no expone (actualmente: templates biométricos de huellas dactilares, tabla `iclock_biodata`).

## Comandos

```bash
# Activar entorno virtual (obligatorio antes de cualquier comando)
source venv/bin/activate

# Correr la aplicación
uvicorn app.main:app --reload
# o
python -m app.main

# Tests
pytest                                                                 # todos
pytest tests/unit/                                                     # solo unit
pytest tests/integration/                                              # solo integration
pytest tests/unit/services/test_biotime_service.py                    # un archivo

# Linting y formato
black app/ tests/
isort app/ tests/
flake8 app/ tests/
mypy app/
```

Configuración de pytest, black, isort y mypy está en `pyproject.toml`.

## Flujo de arranque (desde `app/main.py`)

### 1. Carga de configuración (module-level, antes de todo)
- `app/core/config.py` — `Settings` (pydantic-settings) carga `.env` y luego `.env.{ENVIRONMENT}` como override. La instancia `settings` queda disponible como singleton global.
- Si `TAREAS_HABILITADO=True`: se importa `app/services/tareas/servicio_tareas.py`, lo que a su vez:
  - Crea instancias singleton de `PrecisoClient` y `BioTimeClient`
  - Registra `_tarea_polling()` en el `scheduler` global con `@scheduler.registrar(...)`

### 2. Creación de la app FastAPI
```
FastAPI(title, version, openapi_url, docs_url, redoc_url, lifespan=lifespan)
  └── CORSMiddleware (orígenes de ALLOWED_ORIGINS)
  └── api_router con prefijo API_V1_PREFIX (/api/v1)
        ├── areas.router
        ├── empleado.router
        ├── huellas.router
        ├── marcaciones.router
        └── terminales.router
  └── GET /health  (fuera del prefijo)
```

### 3. Lifespan (arranque)
Cuando el servidor recibe su primera solicitud o arranca uvicorn:

```
lifespan() — startup:
  1. iniciar_conexion_bd()
     ├── asyncpg.create_pool(min=2, max=10) → _pool global
     └── _migrar_constraint_biodata() — verifica/recrea constraint único en iclock_biodata
  2. scheduler.iniciar()  (solo si TAREAS_HABILITADO=True)
     └── asyncio.create_task(_loop_periodico) por cada tarea registrada
         └── polling_tareas_preciso → cada TAREAS_INTERVALO_SEGUNDOS segundos
  yield  ← aplicación disponible para peticiones
```

### 4. Ciclo de vida del scheduler (tareas periódicas)
Cada `TAREAS_INTERVALO_SEGUNDOS` segundos:
```
_tarea_polling()
  └── ServicioTareas.procesar_tareas()
        1. PrecisoClient.obtener_tareas()  → GET /api/tareas (con OAuth2)
        2. _filtrar_tareas_por_ip()        → filtra por TAREAS_IPS_PERMITIR / TAREAS_IPS_IGNORAR
        3. Para cada tarea:
             manejadores.ejecutar(tarea, biotime_client)  → opera contra BioTime
             PrecisoClient.completar_tarea(payload)       → POST /api/completar_tarea
```

### 5. Ciclo de vida por petición HTTP
```
Request HTTP → CORSMiddleware → Router (/api/v1/...) → Endpoint
  └── FastAPI DI resuelve dependencias (dependencias.py):
        ├── BioTimeClient()                    ← nueva instancia por petición
        ├── ServicioEmpleado(client)            ← IEmpleado
        ├── ServicioMarcaciones(client)         ← IMarcaciones
        ├── ServicioHuellas(RepositorioHuellas) ← IHuellas (usa _pool de asyncpg)
        ├── ServicioTerminales(client)          ← ITerminales
        ├── ServicioAreas(client)               ← IAreas
        └── ServicioSincronizacion(client)      ← ISincronizacion
            (o SincronizacionDeshabilitada si BIOTIME_SYNC_HABILITADO=False)
  └── Respuesta serializada con ConfigurableAliasRoute
        └── camelCase o snake_case según API_RESPONSE_CASE
```

### 6. Lifespan (apagado)
```
lifespan() — shutdown:
  1. scheduler.detener()  → cancela todas las asyncio.Task
  2. cerrar_conexion_bd() → _pool.close()
```

## Estructura real

```
app/
├── api/
│   ├── dependencias.py              # Aliases de DI: EmpleadoDependencia, HuellasDependencia, MarcacionesDependencia, SincronizacionDependencia
│   ├── interfaces/
│   │   └── interface_biotime_service.py  # OBSOLETO — archivo legado, no usar
│   └── v1/
│       ├── router.py                # Registra empleado.router, huellas.router y marcaciones.router
│       └── routes/
│           ├── empleado.py          # GET /employees, GET /employees/{id}, POST, PUT, DELETE
│           ├── huellas.py           # GET /huellas, GET /huellas/por-empleado
│           └── marcaciones.py       # GET /marcaciones, GET /marcaciones/por-empleado, DELETE /marcaciones/por-filtro, DELETE /marcaciones/por-id
├── clients/
│   └── biotime_client.py            # Único punto de contacto HTTP con BioTime (get/post/put/patch/delete)
├── core/
│   ├── config.py                    # Settings via pydantic-settings (.env + .env.{ENVIRONMENT})
│   ├── exceptions.py                # BioTimeException y subclases
│   └── logging.py                   # structlog (JSON en prod, consola en dev)
├── db/
│   ├── conexion.py                  # Pool asyncpg (min=2, max=10), ciclo de vida via lifespan
│   └── repositorios/
│       └── repositorio_huellas.py   # Queries SQL directas a iclock_biodata
├── interfaces/
│   ├── empleado/
│   │   └── interface_empleado.py    # IEmpleado (ABC)
│   ├── huellas/
│   │   └── interface_huellas.py     # IHuellas (ABC)
│   ├── marcaciones/
│   │   └── interface_marcaciones.py # IMarcaciones (ABC)
│   └── sincronizacion/
│       └── interface_sincronizacion.py  # ISincronizacion (ABC) + SincronizacionDeshabilitada (Null Object)
├── schemas/
│   ├── base.py                      # BaseDto: alias_generator=to_camel, populate_by_name=True
│   ├── biotime/
│   │   ├── auth.py                  # LoginRequest, LoginResponse
│   │   └── common.py                # PaginatedResponse[T]
│   ├── empleado/
│   │   └── respuesta_empleado.py    # EmployeeDto, EmpleadoCreateUpdateDto, DepartmentDto, PositionDto
│   ├── huellas/
│   │   └── respuesta_huellas.py     # HuellaDto (campos reales de iclock_biodata)
│   ├── marcaciones/
│   │   └── respuesta_marcaciones.py # MarcacionesDto, TerminalDto
│   └── respuesta_comun.py           # ErrorResponse, SuccessResponse (no usados sistemáticamente aún)
├── services/
│   ├── empleado/
│   │   └── servicio_empleado.py     # ServicioEmpleado implements IEmpleado
│   ├── huellas/
│   │   └── servicio_huellas.py      # ServicioHuellas implements IHuellas (usa RepositorioHuellas, no BioTimeClient)
│   ├── marcaciones/
│   │   └── servicio_marcaciones.py  # ServicioMarcaciones implements IMarcaciones
│   └── sincronizacion/
│       └── servicio_sincronizacion.py  # ServicioSincronizacion implements ISincronizacion
├── utils/
│   ├── http_helpers.py              # build_query_params() — implementado pero no usado actualmente
│   └── routing.py                   # ConfigurableAliasRoute: controla camelCase/snake_case por API_RESPONSE_CASE
└── main.py                          # FastAPI app, CORS, lifespan (pool BD), prefijo /api/v1, /health
```

## Endpoints expuestos

### Empleados
| Método   | Path                          | Descripción                                          |
|----------|-------------------------------|------------------------------------------------------|
| GET      | `/api/v1/employees`           | Lista paginada de empleados (`page`, `page_size`)    |
| GET      | `/api/v1/employees/{id}`      | Obtiene un empleado por ID de BioTime                |
| POST     | `/api/v1/employees`           | Crea un empleado + sincroniza terminales             |
| PUT      | `/api/v1/employees/{id}`      | Reemplaza datos de un empleado + sincroniza          |
| DELETE   | `/api/v1/employees/{id}`      | Elimina un empleado + sincroniza (retorna 204)       |

### Marcaciones
| Método   | Path                                   | Descripción                                                      |
|----------|----------------------------------------|------------------------------------------------------------------|
| GET      | `/api/v1/marcaciones`                  | Lista paginada de marcaciones (`page`, `page_size`)              |
| GET      | `/api/v1/marcaciones/por-empleado`     | Filtradas por `codigo_empleado`, `fecha_inicio`, `fecha_fin`     |
| DELETE   | `/api/v1/marcaciones/por-filtro`       | Elimina masivamente por filtro + sincroniza (requiere ≥1 filtro) |
| DELETE   | `/api/v1/marcaciones/por-id`           | Elimina una marcación por `id_marcacion` + sincroniza            |

### Huellas dactilares (desde PostgreSQL, tabla `iclock_biodata`)
| Método   | Path                               | Descripción                                                        |
|----------|------------------------------------|--------------------------------------------------------------------|
| GET      | `/api/v1/huellas`                  | Lista paginada de todas las huellas (`page`, `page_size`)          |
| GET      | `/api/v1/huellas/por-empleado`     | Huellas de un empleado por `empleado_id` (int, FK en iclock_biodata) |

### Sistema
| Método   | Path       | Descripción                                    |
|----------|------------|------------------------------------------------|
| GET      | `/health`  | Health check (fuera del prefijo `/api/v1`)     |

BioTime endpoints internos: `personnel/api/employees/`, `iclock/api/transactions/`, `iclock/api/terminals/`.

## Schemas principales

### HuellaDto — campos reales de `iclock_biodata`
```python
id: int             # ID del registro
employee_id: int    # FK a personnel_employee.id (NO es emp_code, es el ID entero)
bio_index: int      # Índice del dedo/elemento (0-9)
bio_type: int       # Tipo biométrico (1=huella)
bio_no: int         # Número de template
bio_format: int     # Formato del template
valid: int          # 1=válido, 0=inválido
duress: int         # Flag de coacción
bio_tmp: Optional[str]  # Template biométrico en base64
sn: Optional[str]       # Número de serie del terminal de origen
```

> **Importante:** `employee_id` es la FK entera del registro en PostgreSQL, distinto del `emp_code`
> (string como "EMP001") que usa la API REST de BioTime. Para filtrar huellas usar `empleado_id=<int>`.

### EmployeeDto
```python
id: int, emp_code: str, first_name: str, last_name: Optional[str],
department: Optional[DepartmentDto | int], position: Optional[PositionDto | int],
hire_date: Optional[str]
```

### MarcacionesDto
```python
id: int, emp_code: str, punch_time: str, punch_state: str, verify_type: int,
terminal_sn: str, upload_time: str, ...  # más campos opcionales
```

## Patrón de inyección de dependencias

`dependencias.py` define type aliases que FastAPI resuelve automáticamente:

```python
EmpleadoDependencia      = Annotated[IEmpleado,       Depends(obtener_servicio_empleados)]
HuellasDependencia       = Annotated[IHuellas,         Depends(obtener_servicio_huellas)]
MarcacionesDependencia   = Annotated[IMarcaciones,     Depends(obtener_servicio_marcaciones)]
SincronizacionDependencia = Annotated[ISincronizacion, Depends(obtener_servicio_sincronizacion)]
```

- `obtener_servicio_huellas` — crea `RepositorioHuellas(pool)` → `ServicioHuellas(repositorio)` (usa PostgreSQL, no BioTimeClient)
- Los demás servicios crean una nueva instancia de `BioTimeClient` por petición.
- `obtener_servicio_sincronizacion` — retorna `ServicioSincronizacion` o `SincronizacionDeshabilitada` según `BIOTIME_SYNC_HABILITADO`.

## Flujo de autenticación en BioTimeClient

1. Al hacer `get()`/`delete()`/etc., llama `_get_headers()`
2. Si no hay token → `_login()` → POST a `jwt-api-token-auth/` → guarda JWT
3. Si la respuesta es 401 → borra token → reintenta login → reintenta petición (una vez)
4. DELETE 204 → devuelve `{}` vacío
5. Cuerpo vacío o `"\n"` → devuelve `{}` vacío

## Flujo de sincronización de terminales

Se dispara automáticamente tras POST/PUT/DELETE de empleados y DELETE de marcaciones.

1. Obtiene todos los IDs de terminales paginando `iclock/api/terminals/`
2. Para cada terminal, intenta hasta 4 endpoints en orden (distintas versiones de BioTime):
   - `iclock/api/terminals/{id}/sync/`
   - `iclock/api/terminals/{id}/sync_user/`
   - `iclock/api/terminals/{id}/sync_transaction/`
   - `personnel/api/terminal/{id}/sync/`
3. Si `BIOTIME_SYNC_HABILITADO=False` → `SincronizacionDeshabilitada.sincronizar()` no hace nada (Null Object Pattern)

## Formato de respuesta JSON (camelCase / snake_case)

Controlado por `API_RESPONSE_CASE` en `.env`. Implementado en `app/utils/routing.py`:

- `API_RESPONSE_CASE=camel` (default) → respuestas en camelCase (`empCode`, `firstName`, `bioIndex`)
- `API_RESPONSE_CASE=snake` → respuestas en snake_case (`emp_code`, `first_name`, `bio_index`)

Todos los routers usan `route_class=ConfigurableAliasRoute`. El alias se genera en `BaseDto` con `alias_generator=to_camel`.

## Acceso directo a PostgreSQL

Solo se usa PostgreSQL directo para las huellas dactilares (la API REST de BioTime no las expone).

- Pool iniciado en el `lifespan` de `main.py` via `iniciar_conexion_bd()` / `cerrar_conexion_bd()`
- Conexión: `asyncpg`, pool min=2 / max=10
- Tabla por defecto: `iclock_biodata` (configurable con `DB_TABLA_HUELLAS`)
- Queries siempre usan parámetros posicionales (`$1`, `$2`) para evitar SQL injection

## Agregar un nuevo recurso

1. Schema en `app/schemas/<recurso>/respuesta_<recurso>.py`
2. Interfaz en `app/interfaces/<recurso>/interface_<recurso>.py` (heredar ABC)
3. Servicio en `app/services/<recurso>/servicio_<recurso>.py` (implementar interfaz)
4. Endpoint en `app/api/v1/routes/<recurso>.py` (usar `route_class=ConfigurableAliasRoute`)
5. Registrar router en `app/api/v1/router.py`
6. Agregar dependency alias en `app/api/dependencias.py`

Si el recurso requiere BD directa: agregar repositorio en `app/db/repositorios/`.

## Variables de entorno

### Requeridas (sin default)
| Variable           | Descripción                        |
|--------------------|------------------------------------|
| `BIOTIME_BASE_URL` | URL base de BioTime API            |
| `BIOTIME_USERNAME` | Usuario de BioTime                 |
| `BIOTIME_PASSWORD` | Contraseña de BioTime              |
| `DB_PASSWORD`      | Contraseña de PostgreSQL           |

### Opcionales
| Variable                  | Default               | Descripción                                                     |
|---------------------------|-----------------------|-----------------------------------------------------------------|
| `ENVIRONMENT`             | `local`               | Ambiente: `local`, `desarrollo`, `produccion`                   |
| `DEBUG`                   | `False`               | Modo debug                                                      |
| `HOST`                    | `0.0.0.0`             | Host uvicorn                                                    |
| `PORT`                    | `8001`                | Puerto uvicorn                                                  |
| `API_V1_PREFIX`           | `/api/v1`             | Prefijo de la API                                               |
| `ALLOWED_ORIGINS`         | `["*"]`               | CORS: orígenes permitidos                                       |
| `BIOTIME_TIMEOUT`         | `30`                  | Timeout en segundos para requests a BioTime                     |
| `API_RESPONSE_CASE`       | `camel`               | Formato claves JSON: `camel` (empCode) o `snake` (emp_code)     |
| `BIOTIME_SYNC_HABILITADO` | `True`                | Habilita sincronización automática tras operaciones de escritura |
| `DB_HOST`                 | `127.0.0.1`           | Host PostgreSQL                                                 |
| `DB_PUERTO`               | `5432`                | Puerto PostgreSQL                                               |
| `DB_NOMBRE`               | `biotime`             | Nombre de la base de datos                                      |
| `DB_USUARIO`              | `postgres`            | Usuario PostgreSQL                                              |
| `DB_TABLA_HUELLAS`        | `iclock_biodata`      | Tabla de huellas dactilares                                     |
| `LOG_LEVEL`               | `INFO`                | Nivel de logging                                                |

La configuración carga `.env` como base y luego `.env.{ENVIRONMENT}` como override.

## Archivos obsoletos / sin uso

- `app/api/interfaces/interface_biotime_service.py` — interfaz legada `IBioTimeService`, no se importa en ningún lado. Puede eliminarse.
- `app/utils/http_helpers.py` — `build_query_params()` implementada pero no usada. Los servicios construyen `params` manualmente.

---

## Proyectos relacionados

Estos proyectos son parte del mismo ecosistema y en el futuro se integrarán con este servicio.

### PrecisoAPI (`Proyectos/Preciso/precisoapi`)

Sistema integral de gestión de asistencia empresarial. Es el sistema de negocio principal que consume datos de terminales ZKTeco.

**Stack**: PHP 7.1 / Laravel 5.6, Oracle XE, Vue.js, Laravel Passport (OAuth2)

**Qué hace:**
- Gestiona el ciclo completo de RRHH: empleados, locales, turnos, jornadas, planificación semanal
- Registra marcaciones (entrada/salida) capturadas desde terminales biométricos
- Realiza cierres diarios por local y calcula horas extras/suplementarias por quincena
- Genera reportes de asistencia (PDF via JasperReports, Excel via Maatwebsite)
- Audita todos los cambios en BD via sistema de eventos Laravel (`DBModificada` → `LogDB`)

**Comunicación con dispositivos ZKTeco (mecanismo TAREA):**

PrecisoAPI no habla directamente con los terminales. En su lugar usa una tabla de tareas asincrónica:

```
PrecisoAPI escribe en tabla TAREA (instruccion, ip, detalle)
    ↓
Daemon (zkdaemon o PrecisoWFDaemon) hace polling: GET /api/tareas
    ↓
Daemon ejecuta instrucción en el terminal (protocolo ZK)
    ↓
Daemon reporta resultado: POST /api/completar_tarea
```

**Instrucciones de tarea que maneja el daemon:**

| Instrucción | Descripción |
|-------------|-------------|
| `EMPDAT` | Crear/actualizar empleado en terminal |
| `EMPUDT` | Actualizar datos de empleado |
| `EMPDEL` | Eliminar empleado del terminal |
| `EMPMAR` | Leer marcaciones del terminal |
| `EMPMAD` | Leer y borrar marcaciones del terminal |
| `EMPHUE` | Leer templates de huella de un empleado |
| `DELHUE` | Eliminar huella del terminal |
| `REPHUE` | Replicar huella a terminal(es) |
| `COPHUE` | Copiar huella entre empleados |
| `DISDAT` | Leer info del dispositivo (serie, firmware, MAC) |
| `ASGPRV` | Asignar/revocar privilegios de administrador |
| `RESETD` | Reset completo del dispositivo |
| `UPDTFH` | Actualizar fecha/hora del terminal |

**Endpoints clave para integración:**

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/oauth/token` | — | Obtener token OAuth2 (password grant) |
| GET | `/api/tareas` | Bearer | Listar tareas pendientes para el daemon |
| POST | `/api/completar_tarea` | Bearer | Marcar tarea como completada con resultado |
| POST | `/api/marcacion_dispositivo` | — | Recibir marcación desde terminal/daemon |

**Modelo de datos de Tarea:**
```json
{
  "id_tarea": 42,
  "instruccion": "EMPDAT",
  "ip": "192.168.1.10",
  "detalle": "EMP001|Juan Perez|N|0",
  "id_tabla": 7,
  "estado": "E"
}
```

**Serialización de `detalle`:** campos separados por `|`, registros múltiples separados por `&`.

---

### zkdaemon (`Proyectos/Preciso/zkdaemon`)

Daemon Python que actúa como puente entre PrecisoAPI y los terminales biométricos ZKTeco. Es el componente que realmente habla con el hardware.

**Stack**: Python 3.7+, librería `zk` (protocolo ZK propietario sobre UDP/TCP), `requests`

**Qué hace:**
- Hace polling continuo a PrecisoAPI vía HTTP para obtener tareas pendientes
- Por cada tarea, abre una conexión directa al terminal ZKTeco (socket UDP/TCP, puerto 4370)
- Traduce la instrucción de alto nivel a comandos ZK binarios
- Ejecuta la operación en el terminal (leer huellas, crear usuario, leer marcaciones, etc.)
- Reporta el resultado de vuelta a PrecisoAPI
- Registra todo en `/logs/zkpydaemon.log`

**Arquitectura interna:**

```
base.py (entrypoint/loop principal)
    ↓
clientapi.py (ClientApi)
    ├── obtener_token()          → OAuth2 password grant → PrecisoAPI
    ├── obtener_tareas()         → GET /api/tareas → PrecisoAPI
    ├── instruccion_a_ejecutar() → dispatcher dinámico por nombre
    │   └── ejecutar_EMPDAT(), ejecutar_EMPHUE(), ... (15+ métodos)
    └── cerrar_tarea()           → POST /api/completar_tarea → PrecisoAPI
              ↓
devicelib.py (DeviceController)
    ├── conectar()               → ZK(ip, port=4370, timeout=20).connect()
    ├── anadir_empleado()
    ├── leer_marcaciones()
    ├── leer_huella()
    ├── copiar_huella()
    └── eliminar_huella()
              ↓
zk/base.py (ZK class — protocolo propietario)
    ├── Paquetes binarios: header + checksum CRC16
    ├── Sesiones con session_id y reply_id
    ├── Dual UDP/TCP (intenta TCP, fallback UDP)
    └── Comandos: CMD_USER_WRQ(8), CMD_USERTEMP_RRQ(9), CMD_ATTLOG_RRQ(13), ...
              ↓
Terminal ZKTeco (hardware)
    Puerto 4370 UDP/TCP
```

**Modelos de datos internos del protocolo ZK:**

```python
# Usuario en el terminal
User(uid, name, privilege, password, group_id, user_id, card)
# user_id = emp_code de PrecisoAPI (ej: "EMP001")
# privilege: 0=user, 2=enroller, 6=manager, 14=admin

# Marcación capturada
Attendance(uid, user_id, timestamp, status, punch)

# Template biométrico de huella
Finger(uid, fid, valid, template: bytes, size)
# fid = índice del dedo (0-9)
```

**Configuración** (`config.cfg`):
```ini
[RestServer]
url = http://<host>/precisoapi/public/
client_id = <id_oauth>
client_secret = <secret_oauth>
username = <usuario>
password = <clave>
```

**Ejecución:**
```bash
python3 base.py
# o en producción (singleton):
bash daemon.sh
```

---

### Relación entre los tres sistemas

```
[Terminales ZKTeco] ←──protocolo ZK binario──→ [zkdaemon]
                                                      │
                                                   HTTP/OAuth2
                                                      │
                                                 [PrecisoAPI]
                                                 (Laravel/Oracle)
                                                      │
                                              (integración futura)
                                                      │
                                          [Servicio APIs BioTime]  ←──JWT──→ [BioTime]
                                                                                  │
                                                                           [Terminales ZKTeco]
```

- **zkdaemon** → habla directamente con terminales vía protocolo ZK (bajo nivel, sin intermediarios)
- **Servicio APIs BioTime** → habla con terminales a través de BioTime (que hace de broker centralizado)
- **PrecisoAPI** → sistema de negocio que orquesta todo; usa zkdaemon para operaciones en tiempo real y podría usar este servicio para acceder a datos de BioTime
- Los tres proyectos comparten el dominio ZKTeco pero en capas distintas de abstracción

**Diferencia clave respecto a este servicio:**
- Este servicio accede a BioTime (API REST de ZKTeco) y su PostgreSQL
- zkdaemon accede a los terminales directamente (protocolo binario, sin BioTime)
- Ambos pueden coexistir: zkdaemon para operaciones inmediatas en hardware, este servicio para lectura centralizada de datos históricos vía BioTime
