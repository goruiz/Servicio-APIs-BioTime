# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Propósito

Middleware REST que envuelve la API de BioTime (sistema biométrico ZKTeco). Maneja autenticación JWT automáticamente y expone una interfaz limpia y tipada para consumidores externos.

## Comandos

```bash
# Activar entorno virtual (obligatorio antes de cualquier comando)
source venv/bin/activate

# Correr la aplicación
python -m app.main
# o
uvicorn app.main:app --reload

# Tests
pytest                                     # todos los tests
pytest tests/unit/                         # solo unit tests
pytest tests/integration/                  # solo integration tests
pytest tests/unit/services/test_biotime_service.py  # un archivo específico

# Linting y formato
black app/ tests/
isort app/ tests/
flake8 app/ tests/
mypy app/
```

Configuración de pytest, black, isort y mypy está en `pyproject.toml`.

## Arquitectura real (estructura de archivos actual)

El README describe una estructura idealizada que **no coincide** con la estructura real. La estructura real es:

```
app/
├── api/
│   ├── dependencies.py          # Inyección de dependencias (BioTimeServiceDependencia)
│   └── v1/
│       ├── router.py            # Agrega employees.router al api_router
│       └── routes/
│           └── employees.py     # Endpoints GET /employees
├── clients/
│   └── biotime_client.py        # Único punto de contacto con BioTime API
├── core/
│   ├── config.py                # Settings via pydantic-settings (.env)
│   ├── exceptions.py            # BioTimeException y subclases
│   └── logging.py               # structlog (JSON en prod, consola en dev)
├── interfaces/
│   └── interface_biotime_service.py  # IBioTimeService (ABC)
├── schemas/
│   └── biotime/
│       ├── auth.py              # LoginRequest, LoginResponse
│       ├── common.py            # PaginatedResponse[T]
│       └── employee.py          # EmployeeDto, DepartmentDto, PositionDto
├── services/
│   └── biotime_service.py       # BioTimeService implementa IBioTimeService
├── utils/
│   └── http_helpers.py          # build_query_params (actualmente sin usar)
└── main.py                      # FastAPI app, CORS, incluye api_router en /api/v1
```

**Crítico**: las interfaces viven en `app/interfaces/`, no en `app/services/interfaces/`. El import correcto es:
```python
from app.interfaces.interface_biotime_service import IBioTimeService
```

## Flujo de una petición

```
Uvicorn → FastAPI (main.py, configurado al inicio)
        → CORS middleware
        → api_router (/api/v1) → employees.router (/employees)
        → FastAPI resuelve dependencias: BioTimeClient → BioTimeService
        → get_employees(service, page, page_size)
        → service.get_employees() → client.get("personnel/api/employees/")
        → BioTimeClient: ¿token? no → _login() → guarda JWT
        → GET BioTime con Authorization: JWT <token>
        → ¿401? → borra token → _login() → reintenta
        → JSON crudo → parseado a EmployeeDto[] → devuelve result.data
```

## Patrón de inyección de dependencias

Las dependencias se definen en `dependencies.py` como type aliases:

```python
BioTimeServiceDependencia = Annotated[IBioTimeService, Depends(get_biotime_service)]
```

Los endpoints las reciben como parámetro tipado y FastAPI las resuelve automáticamente. Una nueva instancia de `BioTimeClient` y `BioTimeService` se crea por cada petición.

## Agregar un nuevo recurso

1. Schema en `app/schemas/biotime/<recurso>.py`
2. Método abstracto en `app/interfaces/interface_biotime_service.py`
3. Implementación en `app/services/biotime_service.py`
4. Endpoint en `app/api/v1/routes/<recurso>.py`
5. Registrar en `app/api/v1/router.py`
6. Agregar dependency alias en `app/api/dependencies.py`

## Variables de entorno requeridas

`BIOTIME_BASE_URL`, `BIOTIME_USERNAME`, `BIOTIME_PASSWORD` son obligatorias (sin default). El resto tiene defaults. Ver `.env.example`.
