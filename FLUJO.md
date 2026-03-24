# Documentación: Propósito y Flujo de Peticiones

## ¿Para qué sirve este servicio?

Este proyecto es un **servicio intermediario (middleware)** que expone una API REST propia y, por dentro, se comunica con la API de **BioTime** (sistema biométrico de ZKTeco).

**BioTime** es un sistema de gestión de asistencia y control de acceso que usa dispositivos biométricos (huellas, rostro, tarjetas). Tiene su propia API REST, pero exige autenticación JWT en cada petición y devuelve datos en formatos específicos de su plataforma.

Este servicio existe para:

- **Abstraer la complejidad de BioTime**: los consumidores del servicio (otras apps, frontends, integraciones) no necesitan conocer cómo funciona BioTime internamente.
- **Centralizar la autenticación**: el servicio maneja el login y el refresco de tokens JWT contra BioTime de forma automática y transparente.
- **Normalizar los datos**: transforma las respuestas crudas de BioTime en DTOs tipados y validados con Pydantic.
- **Ofrecer una interfaz estable**: si BioTime cambia su API, solo se actualiza este servicio; los consumidores externos no se ven afectados.
- **Agregar logging estructurado**: todas las operaciones quedan registradas en formato JSON (producción) o legible (desarrollo).

---

## Flujo completo de una petición

A continuación se describe paso a paso lo que ocurre desde que un cliente externo hace una petición hasta que recibe la respuesta.

### Ejemplo: `GET /api/v1/employees?page=1&page_size=10`

```
Cliente externo
     │
     │  GET /api/v1/employees?page=1&page_size=10
     ▼
┌─────────────────────────────────────────────────────────────┐
│  1. FastAPI + Middleware CORS  (app/main.py)                 │
│     - Valida que el origen (Origin header) esté permitido   │
│     - Si no está permitido, corta con 403                   │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Router principal  (app/api/v1/router.py)                │
│     - El prefijo /api/v1 dirige al api_router               │
│     - api_router redirige /employees al router de empleados │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Inyección de dependencias  (app/api/dependencies.py)    │
│     FastAPI resuelve automáticamente:                       │
│       a) get_biotime_client()  → crea BioTimeClient()       │
│       b) get_biotime_service() → crea BioTimeService(client)│
│     El endpoint recibe el servicio listo para usar          │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Endpoint  (app/api/v1/routes/employees.py)              │
│     - Valida query params: page ≥ 1, page_size entre 1-100  │
│     - Llama: await service.get_employees(page, page_size)   │
│     - Captura BioTimeException → HTTPException apropiada    │
│     - Captura Exception genérica → 500                      │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Servicio  (app/services/implementations/biotime_service)│
│     - Arma params: {"page": 1, "page_size": 10}             │
│     - Llama: await client.get("personnel/api/employees/",   │
│                                params=params)               │
│     - Parsea la respuesta cruda a EmployeeDto[]             │
│     - Construye PaginatedResponse[EmployeeDto]              │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  6. Cliente HTTP  (app/clients/biotime_client.py)           │
│                                                             │
│  ¿Tiene token JWT almacenado?                               │
│       NO → llama _login()                                   │
│              POST {BIOTIME_BASE_URL}/jwt-api-token-auth/    │
│              body: {username, password}                     │
│              guarda self._token = response.token            │
│       SÍ → usa token existente                              │
│                                                             │
│  Construye cliente httpx con header:                        │
│       Authorization: JWT <token>                            │
│                                                             │
│  GET {BIOTIME_BASE_URL}/personnel/api/employees/            │
│       ?page=1&page_size=10                                  │
│                                                             │
│  ¿Respuesta 401? (token expirado)                           │
│       SÍ → limpia token, llama _login() otra vez, reintenta │
│       NO → continúa                                         │
│                                                             │
│  Llama response.raise_for_status() (lanza si 4xx/5xx)      │
│  Devuelve response.json() al servicio                       │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  7. BioTime API  (sistema externo)                          │
│     Responde con JSON:                                      │
│     {                                                       │
│       "count": 150,                                         │
│       "next": ".../?page=2",                                │
│       "previous": null,                                     │
│       "data": [ { "id": 1, "emp_code": "EMP001", ... } ]   │
│     }                                                       │
└───────────────────┬─────────────────────────────────────────┘
                    │ (vuelta al servicio)
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  8. Parseo y construcción de DTOs  (biotime_service.py)     │
│     - Itera data[] → EmployeeDto(**emp) por cada elemento   │
│     - Pydantic valida y tipifica los campos                 │
│     - Construye PaginatedResponse[EmployeeDto] con          │
│       count, next, previous y la lista de DTOs              │
└───────────────────┬─────────────────────────────────────────┘
                    │ (vuelta al endpoint)
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  9. Endpoint devuelve result.data  (employees.py)           │
│     - Extrae solo la lista de EmployeeDto del paginated     │
│     - FastAPI serializa automáticamente via Pydantic        │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
Cliente externo recibe:
[
  {
    "id": 1,
    "emp_code": "EMP001",
    "first_name": "Juan",
    "last_name": "Pérez",
    "department": { "id": 1, "dept_code": "IT", "dept_name": "Tecnología" },
    "position": { "id": 2, "position_code": "DEV", "position_name": "Desarrollador" },
    "hire_date": "2024-01-15"
  },
  ...
]
```

---

## Manejo de errores

| Situación | Excepción interna | HTTP devuelto |
|---|---|---|
| Credenciales de BioTime incorrectas | `BioTimeAuthenticationError` | `401 Unauthorized` |
| BioTime no responde / red caída | `BioTimeConnectionError` | `502 Bad Gateway` |
| Recurso no encontrado en BioTime | `BioTimeNotFoundError` | `404 Not Found` |
| Datos inválidos | `BioTimeValidationError` | `422 Unprocessable Entity` |
| Error no contemplado | `Exception` genérica | `500 Internal Server Error` |

---

## Diagrama simplificado de capas

```
┌──────────────────────────────────────────────┐
│  Cliente externo (frontend, otra app, Postman)│
└──────────────────┬───────────────────────────┘
                   │ HTTP
┌──────────────────▼───────────────────────────┐
│  Capa de presentación  (app/api/)             │
│  • Middleware CORS                            │
│  • Routers y endpoints FastAPI               │
│  • Validación de parámetros (Pydantic)        │
│  • Inyección de dependencias                  │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│  Capa de aplicación  (app/services/)          │
│  • IBioTimeService (interfaz/contrato)        │
│  • BioTimeService  (lógica de negocio)        │
│  • Parseo y transformación de datos           │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│  Capa de infraestructura  (app/clients/)      │
│  • BioTimeClient (HTTP con httpx)             │
│  • Autenticación JWT automática               │
│  • Reintento ante token expirado              │
└──────────────────┬───────────────────────────┘
                   │ HTTPS
┌──────────────────▼───────────────────────────┐
│  BioTime API  (sistema externo ZKTeco)        │
└──────────────────────────────────────────────┘
```

---

## Endpoints disponibles

### `GET /health`
Verifica que el servicio esté en pie. No requiere autenticación ni conexión con BioTime.

**Respuesta:**
```json
{
  "status": "healthy",
  "service": "Servicio APIs BioTime",
  "version": "1.0.0"
}
```

---

### `GET /api/v1/employees`
Obtiene la lista paginada de empleados registrados en BioTime.

**Query params:**

| Parámetro | Tipo | Default | Rango | Descripción |
|---|---|---|---|---|
| `page` | int | `1` | ≥ 1 | Número de página |
| `page_size` | int | `10` | 1 – 100 | Registros por página |

**Respuesta exitosa (200):**
```json
[
  {
    "id": 1,
    "emp_code": "EMP001",
    "first_name": "Juan",
    "last_name": "Pérez",
    "department": {
      "id": 1,
      "dept_code": "IT",
      "dept_name": "Tecnología"
    },
    "position": {
      "id": 2,
      "position_code": "DEV",
      "position_name": "Desarrollador"
    },
    "hire_date": "2024-01-15"
  }
]
```

**Errores posibles:**
```json
// 401 - Error de autenticación con BioTime
{ "detail": { "error": "Error de autenticación con BioTime", "status_code": 401 } }

// 502 - BioTime no disponible
{ "detail": { "error": "Error al conectar con BioTime", "status_code": 502 } }

// 500 - Error inesperado
{ "detail": { "error": "Error interno del servidor", "detail": "..." } }
```

---

## Documentación interactiva

Con el servicio corriendo, la documentación Swagger y ReDoc están disponibles en:

- **Swagger UI**: `http://localhost:8001/api/v1/docs`
- **ReDoc**: `http://localhost:8001/api/v1/redoc`
- **OpenAPI JSON**: `http://localhost:8001/api/v1/openapi.json`

---

## Variables de entorno requeridas

| Variable | Descripción | Ejemplo |
|---|---|---|
| `BIOTIME_BASE_URL` | URL base de la API de BioTime (con `/` al final) | `http://192.168.1.100:8001/` |
| `BIOTIME_USERNAME` | Usuario administrador de BioTime | `admin` |
| `BIOTIME_PASSWORD` | Contraseña del usuario de BioTime | `secret` |
| `BIOTIME_TIMEOUT` | Timeout en segundos para peticiones a BioTime | `30` |
| `DEBUG` | Activa logs legibles y recarga automática | `False` |
| `LOG_LEVEL` | Nivel de logging (`DEBUG`, `INFO`, `WARNING`) | `INFO` |
| `ALLOWED_ORIGINS` | Orígenes permitidos para CORS (JSON array) | `["*"]` |
