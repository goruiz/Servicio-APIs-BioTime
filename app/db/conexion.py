"""
Gestión del pool de conexiones a PostgreSQL.
El pool se inicia al arrancar la aplicación y se cierra al apagarla.
"""
import asyncpg

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_pool: asyncpg.Pool | None = None


async def iniciar_pool() -> None:
    """Crea el pool de conexiones a PostgreSQL. Llamar en el startup de FastAPI."""
    global _pool
    logger.info(
        "Iniciando pool de conexiones a PostgreSQL",
        host=settings.DB_HOST,
        puerto=settings.DB_PUERTO,
        base_datos=settings.DB_NOMBRE,
    )
    _pool = await asyncpg.create_pool(
        host=settings.DB_HOST,
        port=settings.DB_PUERTO,
        database=settings.DB_NOMBRE,
        user=settings.DB_USUARIO,
        password=settings.DB_PASSWORD,
        min_size=2,
        max_size=10,
    )
    logger.info("Pool de PostgreSQL iniciado correctamente")


async def cerrar_pool() -> None:
    """Cierra el pool de conexiones. Llamar en el shutdown de FastAPI."""
    global _pool
    if _pool:
        await _pool.close()
        logger.info("Pool de PostgreSQL cerrado")


def obtener_pool() -> asyncpg.Pool:
    """Devuelve el pool activo. Lanza error si no fue inicializado."""
    if _pool is None:
        raise RuntimeError("El pool de PostgreSQL no está inicializado")
    return _pool
