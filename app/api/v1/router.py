"""
Router principal de la API v1.
Incluye todos los routers de la versión 1 de la API.
"""
from fastapi import APIRouter

from app.api.v1.routes import areas, empleado, huellas, marcaciones, terminales

api_router = APIRouter()

# Incluir routers de cada recurso
api_router.include_router(areas.router)
api_router.include_router(empleado.router)
api_router.include_router(huellas.router)
api_router.include_router(marcaciones.router)
api_router.include_router(terminales.router)
