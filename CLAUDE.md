# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Propósito

Este proyecto es un servicio middleware REST para conectarse a las APIs de **BioTime**, la aplicación de gestión de asistencia y acceso de **ZKTeco** (fabricante de dispositivos biométricos: lectores de huella dactilar, reconocimiento facial, tarjetas RFID, etc.).

BioTime centraliza los registros de marcaciones (entradas/salidas) capturados por los terminales biométricos ZKTeco y expone una API REST propia. Este middleware actúa como capa de integración: maneja autenticación JWT contra BioTime de forma automática y transparente, y expone una interfaz limpia y tipada para que otros sistemas consuman los datos sin preocuparse por los detalles del protocolo de BioTime.

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
│   ├── dependencias.py              # Aliases de dependencias (EmpleadoDependencia, MarcacionesDependencia)
│   ├── interfaces/
│   │   └── interface_biotime_service.py  # OBSOLETO — archivo legado, no usar
│   └── v1/
│       ├── router.py                # Registra empleado.router y marcaciones.router
│       └── routes/
│           ├── empleado.py          # GET /employees
│           └── marcaciones.py       # GET /marcaciones, GET /marcaciones/por-empleado, DELETE /marcaciones/por-id
├── clients/
│   └── biotime_client.py            # Único punto de contacto HTTP con BioTime (get/post/put/patch/delete)
├── core/
│   ├── config.py                    # Settings via pydantic-settings (.env)
│   ├── exceptions.py                # BioTimeException y subclases
│   └── logging.py                   # structlog (JSON en prod, consola en dev)
├── interfaces/
│   ├── empleado/
│   │   └── interface_empleado.py    # IEmpleado (ABC)
│   └── marcaciones/
│       └── interface_marcaciones.py # IMarcaciones (ABC)
├── schemas/
│   ├── biotime/
│   │   ├── auth.py                  # LoginRequest, LoginResponse
│   │   └── common.py                # PaginatedResponse[T]
│   ├── empleado/
│   │   └── respuesta_empleado.py    # EmployeeDto, DepartmentDto, PositionDto
│   └── marcaciones/
│       └── respuesta_marcaciones.py # MarcacionesDto
├── services/
│   ├── empleado/
│   │   └── servicio_empleado.py     # ServicioEmpleado implements IEmpleado
│   └── marcaciones/
│       └── servicio_marcaciones.py  # ServicioMarcaciones implements IMarcaciones
├── utils/
│   └── http_helpers.py              # build_query_params (sin usar actualmente)
└── main.py                          # FastAPI app, CORS, prefijo /api/v1
```

## Endpoints expuestos

| Método   | Path                              | Descripción                              |
|----------|-----------------------------------|------------------------------------------|
| GET      | `/api/v1/employees`               | Lista paginada de empleados              |
| GET      | `/api/v1/marcaciones`             | Lista paginada de marcaciones            |
| GET      | `/api/v1/marcaciones/por-empleado`| Marcaciones filtradas por `emp_code` y fechas |
| DELETE   | `/api/v1/marcaciones/por-id`      | Elimina una marcación por ID             |

BioTime endpoints internos: `personnel/api/employees/` y `iclock/api/transactions/`.

## Patrón de inyección de dependencias

`dependencias.py` define type aliases que FastAPI resuelve automáticamente:

```python
EmpleadoDependencia = Annotated[IEmpleado, Depends(obtener_servicio_empleados)]
MarcacionesDependencia = Annotated[IMarcaciones, Depends(obtener_servicio_marcaciones)]
```

Cada petición crea una nueva instancia de `BioTimeClient` → `Servicio*`.

## Flujo de autenticación en BioTimeClient

1. Al hacer `get()`/`delete()`/etc., llama `_get_headers()`
2. Si no hay token → `_login()` → POST a `jwt-api-token-auth/` → guarda JWT
3. Si la respuesta es 401 → borra token → reintenta login → reintenta petición
4. DELETE 204 → devuelve `{}` vacío

## Agregar un nuevo recurso

1. Schema en `app/schemas/<recurso>/respuesta_<recurso>.py`
2. Interfaz en `app/interfaces/<recurso>/interface_<recurso>.py` (heredar ABC)
3. Servicio en `app/services/<recurso>/servicio_<recurso>.py` (implementar interfaz)
4. Endpoint en `app/api/v1/routes/<recurso>.py`
5. Registrar router en `app/api/v1/router.py`
6. Agregar dependency alias en `app/api/dependencias.py`

## Variables de entorno

Requeridas (sin default): `BIOTIME_BASE_URL`, `BIOTIME_USERNAME`, `BIOTIME_PASSWORD`.
Ver `.env.example` para el resto de opciones (`PORT`, `DEBUG`, `LOG_LEVEL`, `ALLOWED_ORIGINS`, etc.).
