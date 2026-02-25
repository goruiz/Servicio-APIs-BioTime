"""
Gestión del pool de conexiones a PostgreSQL.
El pool se inicia al arrancar la aplicación y se cierra al apagarla.
"""
import asyncpg

from app.core.config import settings

_pool: asyncpg.Pool | None = None


async def iniciar_pool() -> None:
    """Crea el pool de conexiones a PostgreSQL. Llamar en el startup de FastAPI."""
    global _pool
    print(f"[BD] Conectando a {settings.DB_HOST}:{settings.DB_PUERTO}/{settings.DB_NOMBRE}...")
    _pool = await asyncpg.create_pool(
        host=settings.DB_HOST,
        port=settings.DB_PUERTO,
        database=settings.DB_NOMBRE,
        user=settings.DB_USUARIO,
        password=settings.DB_PASSWORD,
        min_size=2,
        max_size=10,
    )
    print(f"[BD] Conectado — {settings.DB_HOST}:{settings.DB_PUERTO}/{settings.DB_NOMBRE}")


async def cerrar_pool() -> None:
    """Cierra el pool de conexiones. Llamar en el shutdown de FastAPI."""
    global _pool
    if _pool:
        await _pool.close()


def obtener_pool() -> asyncpg.Pool:
    """Devuelve el pool activo. Lanza error si no fue inicializado."""
    if _pool is None:
        raise RuntimeError("El pool de PostgreSQL no está inicializado")
    return _pool
