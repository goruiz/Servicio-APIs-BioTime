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

- Pool iniciado en el `lifespan` de `main.py` via `iniciar_pool()` / `cerrar_pool()`
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
| `PORT`                    | `8000`                | Puerto uvicorn                                                  |
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
