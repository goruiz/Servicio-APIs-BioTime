# Documentación: Flujo de Arranque del Servicio

Describe qué código se ejecuta y en qué orden desde que se lanza el proceso
hasta que el servidor está listo y el scheduler de tareas está corriendo.

---

## Comando de inicio

```bash
python -m app.main
```

---

## FASE 1 — Python carga `main.py` (sincrónico)

Todo el código que está **fuera de funciones** en cada módulo se ejecuta en este
momento, de arriba a abajo, antes de que el servidor arranque.

```
python -m app.main
│
├─ 1. import app.core.config
│       └─ Settings()
│          ├─ lee .env (valores base)
│          ├─ lee .env.local / .env.desarrollo / .env.produccion (según ENVIRONMENT)
│          └─ Pydantic valida que todas las variables requeridas existan
│             (si falta BIOTIME_BASE_URL, DB_PASSWORD, etc. → error aquí y el proceso termina)
│
├─ 2. import app.core.logging
│       └─ (solo define setup_logging y get_logger, no ejecuta nada)
│
├─ 3. import app.core.scheduler
│       └─ Scheduler.__init__()
│          ├─ self._tareas = []          ← lista de tareas registradas (vacía)
│          └─ self._asyncio_tasks = []  ← lista de loops activos (vacía)
│          scheduler está creado pero NO está corriendo
│
├─ 4. import app.db.conexion
│       └─ _pool = None                 ← sin conexión a PostgreSQL todavía
│
├─ 5. setup_logging()
│       ├─ logging.basicConfig(level=INFO, stream=stdout)
│       └─ structlog.configure(...)
│          En DEBUG: salida legible por consola
│          En producción: salida en formato JSON
│
├─ 6. logger = get_logger("app.main")
│
├─ 7. if settings.TAREAS_HABILITADO:   ← True por defecto
│       └─ import app.services.tareas.servicio_tareas
│               │
│               ├─ import app.clients.biotime_client
│               │       └─ (solo define BioTimeClient, no instancia)
│               │
│               ├─ import app.clients.preciso_client
│               │       └─ (solo define PrecisoClient, no instancia)
│               │
│               ├─ import app.services.tareas.manejadores
│               │       └─ (define las 14 funciones manejar_*, no ejecuta nada)
│               │
│               ├─ _preciso_client = PrecisoClient()
│               │       ├─ self._token = None        ← sin autenticar todavía
│               │       ├─ self._base_url = settings.PRECISO_BASE_URL
│               │       └─ self._timeout = settings.PRECISO_TIMEOUT
│               │
│               ├─ _biotime_client = BioTimeClient()
│               │       ├─ self._token = None        ← sin autenticar todavía
│               │       ├─ self._base_url = settings.BIOTIME_BASE_URL
│               │       └─ self._timeout = settings.BIOTIME_TIMEOUT
│               │
│               ├─ _servicio = ServicioTareas(_preciso_client, _biotime_client)
│               │       ├─ self._preciso = _preciso_client
│               │       └─ self._biotime = _biotime_client
│               │
│               └─ @scheduler.registrar("polling_tareas_preciso", intervalo_segundos=60)
│                       └─ scheduler._tareas.append({
│                              nombre:    "polling_tareas_preciso",
│                              intervalo: 60,
│                              funcion:   _procesar_cola_de_tareas   ← referencia a la función
│                          })
│                          scheduler._tareas ahora tiene 1 elemento
│                          El loop NO ha empezado todavía
│
├─ 8. app = FastAPI(lifespan=lifespan, ...)
│       └─ registra que al arrancar debe llamar a lifespan()
│
├─ 9. app.add_middleware(CORSMiddleware)
│
└─ 10. app.include_router(api_router)
        └─ registra todas las rutas HTTP:
           GET  /api/v1/employees
           POST /api/v1/employees
           GET  /api/v1/marcaciones
           GET  /api/v1/huellas
           GET  /api/v1/terminales
           GET  /health
           ...
```

**Al final de la Fase 1:** todo está configurado en memoria. Sin conexiones abiertas,
sin loops corriendo, sin autenticaciones realizadas.

---

## FASE 2 — Uvicorn arranca y ejecuta el `lifespan` (asincrónico)

Uvicorn toma el control, inicializa el event loop de asyncio y llama al bloque
de startup del `lifespan` (el código antes del `yield`).

```
uvicorn arranca el event loop de asyncio
│
└─ lifespan(app)  →  ejecuta hasta el yield
        │
        ├─ await iniciar_conexion_bd()
        │       ├─ logger.info("Iniciando pool de conexiones a PostgreSQL")
        │       ├─ asyncpg.create_pool(host, port, database, user, password,
        │       │                      min_size=2, max_size=10)
        │       │       └─ abre 2 conexiones TCP reales a PostgreSQL
        │       │          (si el servidor no responde → error aquí)
        │       ├─ _pool = <Pool con 2 conexiones listas>
        │       └─ logger.info("Pool de PostgreSQL iniciado correctamente")
        │
        └─ scheduler.iniciar()
                ├─ for tarea in self._tareas:    ← 1 tarea: "polling_tareas_preciso"
                │       └─ asyncio.create_task(
                │              _loop_periodico(tarea),
                │              name="polling_tareas_preciso"
                │          )
                │          Crea una coroutine concurrente en el event loop.
                │          No espera a que termine, continúa inmediatamente.
                │
                └─ logger.info("Scheduler iniciado", total_tareas=1)

yield  ←  uvicorn anuncia que el servidor está listo

    INFO: Application startup complete.
    INFO: Uvicorn running on http://0.0.0.0:8000
```

---

## FASE 3 — El loop periódico empieza a correr (en background)

El `asyncio.create_task` creado en la Fase 2 empieza a ejecutarse en el event loop
en cuanto uvicorn cede el control. Corre concurrentemente con las peticiones HTTP.

```
_loop_periodico(tarea="polling_tareas_preciso")
│
└─ logger.info("Tarea periódica iniciada", intervalo_segundos=60)
│
└─ while True:  ←  loop infinito
        │
        ├─ await _procesar_cola_de_tareas()
        │       └─ await _servicio.procesar_tareas()
        │               │
        │               ├─ logger.info("Consultando tareas en Preciso...")
        │               │
        │               ├─ await self._preciso.obtener_tareas()
        │               │       └─ await self._preciso._request("GET", "api/tareas")
        │               │               └─ await self._preciso._get_headers()
        │               │                       └─ self._token es None
        │               │                               └─ await self._preciso._login()
        │               │                                       ├─ POST /oauth/token
        │               │                                       │  {grant_type, client_id,
        │               │                                       │   client_secret, username,
        │               │                                       │   password}
        │               │                                       └─ self._token = "eyJ..."
        │               │               └─ GET /api/tareas
        │               │                  Authorization: Bearer eyJ...
        │               │               └─ {"tareas": [{id_tarea, ip, instruccion, ...}]}
        │               │       └─ return [TareaDto(...), TareaDto(...)]
        │               │
        │               ├─ (si no hay tareas)
        │               │       └─ logger.info("Sin tareas pendientes en Preciso")
        │               │       └─ return   ←  espera al próximo ciclo
        │               │
        │               └─ (si hay tareas) for tarea in tareas:
        │                       │
        │                       ├─ await manejadores.ejecutar(tarea, self._biotime)
        │                       │       └─ busca el manejador según tarea.instruccion
        │                       │
        │                       │       Ejemplo: instruccion = "EMPMAR"
        │                       │       └─ await manejar_empmar(tarea, client)
        │                       │               ├─ await _obtener_sn_por_ip(client, tarea.ip)
        │                       │               │       └─ GET /iclock/api/terminals/
        │                       │               │          busca ip_address == tarea.ip
        │                       │               │          return "SN_DEL_TERMINAL"
        │                       │               ├─ GET /iclock/api/transactions/
        │                       │               │       ?terminal_sn=SN_DEL_TERMINAL
        │                       │               │       &start_time=hace 24 horas
        │                       │               └─ return CompletarTareaPayload(
        │                       │                      id_tarea=42,
        │                       │                      instruccion="EMPMAR",
        │                       │                      respuesta="001|2026-02-25 08:30:00&..."
        │                       │                  )
        │                       │
        │                       └─ await self._preciso.completar_tarea(payload)
        │                               └─ POST /api/completar_tarea
        │                                  {id_tarea, instruccion, respuesta}
        │                               └─ Preciso actualiza tarea: estado 'E' → 'T'
        │
        └─ await asyncio.sleep(60)
           ←  el loop se "duerme" 60 segundos
              durante este tiempo FastAPI atiende peticiones HTTP con normalidad
              al cumplirse los 60 segundos vuelve al inicio del while True
```

---

## Línea de tiempo completa

```
t = 0s    python -m app.main
          │  Fase 1: carga módulos, valida config, registra tarea en scheduler
          ▼
t = 0s    uvicorn arranca
          │  Fase 2: abre pool PostgreSQL, lanza loop en background
          ▼
t = 0s    servidor listo en http://0.0.0.0:8000
          │
          ├──────────────────────────────────────────────────────────────────►
          │   FastAPI atiende peticiones HTTP (GET /empleados, POST /huellas...)
          │
          │  Fase 3: loop periódico empieza inmediatamente
          │  login en Preciso → GET tareas → ejecuta cada tarea → POST completar
          │  (tarda ~2-5 segundos dependiendo de cuántas tareas haya)
          ▼
t = ~3s   loop entra en asyncio.sleep(60)

t = ~63s  loop despierta → GET tareas → ...

t = ~123s loop despierta → GET tareas → ...

          (y así indefinidamente mientras el proceso esté corriendo)
```

---

## Comportamiento ante errores en el arranque

| Error | Momento | Consecuencia |
|---|---|---|
| Variable de entorno faltante (`BIOTIME_BASE_URL`, etc.) | Fase 1 — `Settings()` | El proceso termina inmediatamente con `ValidationError` |
| PostgreSQL no disponible | Fase 2 — `iniciar_conexion_bd()` | El proceso termina, el servidor no arranca |
| Preciso no disponible | Fase 3 — primer ciclo | Se loguea el error, el loop sigue intentando cada 60 segundos |
| BioTime no disponible | Fase 3 — al ejecutar una tarea | Se loguea el error para esa tarea, las demás siguen procesándose |
| Token expirado (Preciso o BioTime) | Fase 3 — cualquier petición | Se renueva automáticamente con un re-login y se reintenta |

---

## Archivos involucrados en el arranque

```
app/
├── main.py                              ← punto de entrada, orquesta todo
├── core/
│   ├── config.py                        ← carga variables de entorno (.env)
│   ├── logging.py                       ← configura structlog
│   └── scheduler.py                    ← gestiona los loops periódicos
├── db/
│   └── conexion.py                     ← abre el pool de PostgreSQL
├── clients/
│   ├── biotime_client.py               ← cliente HTTP para BioTime (JWT)
│   └── preciso_client.py               ← cliente HTTP para Preciso (OAuth2)
└── services/tareas/
    ├── servicio_tareas.py              ← orquestador + registro en scheduler
    └── manejadores.py                  ← lógica por cada instrucción de tarea
```
