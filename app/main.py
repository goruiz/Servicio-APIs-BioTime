"""
Punto de entrada principal de la aplicación FastAPI.
Servicio de APIs para BioTime - Sistema de gestión biométrica ZKTeco.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.scheduler import scheduler
from app.db.conexion import cerrar_pool, iniciar_pool


if settings.TAREAS_HABILITADO:
    import app.services.tareas.servicio_tareas  # noqa: F401
else:
    print("[App] Scheduler deshabilitado (TAREAS_HABILITADO=False)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await iniciar_pool()

    if settings.TAREAS_HABILITADO:
        scheduler.iniciar()

    yield

    scheduler.detener()
    await cerrar_pool()
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

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
