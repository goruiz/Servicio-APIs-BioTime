"""
Repositorio de huellas dactilares.
Ejecuta queries SQL directamente sobre la base de datos de BioTime.
La tabla se configura con DB_TABLA_HUELLAS en .env (default: biodata_biotemplate).
"""
import asyncpg

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RepositorioHuellas:

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool
        self._tabla = settings.DB_TABLA_HUELLAS

    async def obtener_huellas(
        self, page: int = 1, page_size: int = 10
    ) -> tuple[int, list[dict]]:
        """Devuelve (total, registros) de todas las huellas paginadas."""
        offset = (page - 1) * page_size
        async with self._pool.acquire() as conn:
            total: int = await conn.fetchval(f"SELECT COUNT(*) FROM {self._tabla}")
            filas = await conn.fetch(
                f"SELECT * FROM {self._tabla} ORDER BY id LIMIT $1 OFFSET $2",
                page_size,
                offset,
            )
        return total, [dict(fila) for fila in filas]

    async def obtener_huellas_por_empleado(
        self, codigo_empleado: str, page: int = 1, page_size: int = 10
    ) -> tuple[int, list[dict]]:
        """Devuelve (total, registros) de las huellas de un empleado paginadas."""
        offset = (page - 1) * page_size
        async with self._pool.acquire() as conn:
            total: int = await conn.fetchval(
                f"SELECT COUNT(*) FROM {self._tabla} WHERE emp_code = $1",
                codigo_empleado,
            )
            filas = await conn.fetch(
                f"SELECT * FROM {self._tabla} WHERE emp_code = $1 ORDER BY id LIMIT $2 OFFSET $3",
                codigo_empleado,
                page_size,
                offset,
            )
        return total, [dict(fila) for fila in filas]
