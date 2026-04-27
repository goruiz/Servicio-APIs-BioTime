"""
Punto de entrada principal de la aplicación FastAPI.
Servicio de APIs para BioTime - Sistema de gestión biométrica ZKTeco.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.notificaciones import notificar, notificar_sync
from app.core.scheduler import scheduler
from app.db.conexion import cerrar_conexion_bd, iniciar_conexion_bd

# Flag para saber si el lifespan completó su apagado limpio.
# Si al salir del proceso este flag es False, significa que el servicio
# terminó de forma inesperada (crash, kill, excepción no controlada).
_apagado_limpio = False


if settings.TAREAS_HABILITADO:
    import app.services.tareas.servicio_tareas  # noqa: F401
else:
    print("[App] Scheduler deshabilitado (TAREAS_HABILITADO=False)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(
        f"[App] Entorno: {settings.ENVIRONMENT} | "
        f"Debug: {settings.DEBUG} | "
        f"Host: {settings.HOST}:{settings.PORT}"
    )

    try:
        await iniciar_conexion_bd()

        if settings.TAREAS_HABILITADO:
            scheduler.iniciar()

        await notificar(
            "Servicio iniciado",
            f"Entorno: {settings.ENVIRONMENT}",
        )
    except Exception as e:
        await notificar(
            "Error al iniciar el servicio",
            f"{type(e).__name__}: {e}",
        )
        raise

    yield

    global _apagado_limpio
    scheduler.detener()
    await cerrar_conexion_bd()
    await notificar(
        "Servicio detenido",
        f"Entorno: {settings.ENVIRONMENT}",
    )
    _apagado_limpio = True
    print("[App] Servicio detenido")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Servicio de APIs para conectarse con BioTime",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["Health"])
async def health_check():
    """Endpoint de health check."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


if __name__ == "__main__":
    import uvicorn

    try:
        uvicorn.run(
            "app.main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG,
            log_level="info",
        )
    except Exception as e:
        notificar_sync(
            "Servicio caido por error critico",
            f"{type(e).__name__}: {e}",
        )
    finally:
        if not _apagado_limpio:
            notificar_sync(
                "Servicio detenido inesperadamente",
                f"El proceso termino sin completar el apagado normal.\nEntorno: {settings.ENVIRONMENT}",
            )