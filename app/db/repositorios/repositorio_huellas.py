"""
Repositorio de huellas dactilares.
Ejecuta queries SQL directamente sobre la tabla iclock_biodata de BioTime.
La tabla se configura con DB_TABLA_HUELLAS en .env (default: iclock_biodata).
"""
import asyncpg

from app.core.config import settings


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
        self, empleado_id: int, page: int = 1, page_size: int = 10
    ) -> tuple[int, list[dict]]:
        """Devuelve (total, registros) de las huellas de un empleado paginadas."""
        offset = (page - 1) * page_size
        async with self._pool.acquire() as conn:
            total: int = await conn.fetchval(
                f"SELECT COUNT(*) FROM {self._tabla} WHERE employee_id = $1",
                empleado_id,
            )
            filas = await conn.fetch(
                f"SELECT * FROM {self._tabla} WHERE employee_id = $1 ORDER BY id LIMIT $2 OFFSET $3",
                empleado_id,
                page_size,
                offset,
            )
        return total, [dict(fila) for fila in filas]

    async def obtener_templates_por_empleado(self, employee_id: int) -> list[dict]:
        """Devuelve los campos necesarios de templates no nulos de un empleado (sin paginación)."""
        async with self._pool.acquire() as conn:
            filas = await conn.fetch(
                f"SELECT bio_tmp, bio_index, valid FROM {self._tabla} WHERE employee_id = $1 AND bio_tmp IS NOT NULL ORDER BY id",
                employee_id,
            )
        return [dict(fila) for fila in filas]

    async def obtener_templates_completos_por_empleado(self, employee_id: int) -> list[dict]:
        """Devuelve todos los campos necesarios para copiar templates de un empleado."""
        async with self._pool.acquire() as conn:
            filas = await conn.fetch(
                f"""SELECT employee_id, bio_index, bio_type, bio_no, bio_format,
                           major_ver, minor_ver, valid, duress, bio_tmp
                    FROM {self._tabla}
                    WHERE employee_id = $1 AND bio_tmp IS NOT NULL
                    ORDER BY bio_index, bio_no""",
                employee_id,
            )
        return [dict(fila) for fila in filas]

    async def insertar_o_actualizar_template(
        self,
        employee_id: int,
        bio_index: int,
        bio_type: int,
        bio_no: int,
        bio_format: int,
        major_ver: str,
        minor_ver: str,
        valid: int,
        duress: int,
        bio_tmp: str,
        sn: str,
    ) -> None:
        """Inserta un template en iclock_biodata con el sn del terminal destino.
        Si ya existe un registro para ese empleado+dedo, actualiza bio_tmp, valid y sn
        (el sn pasa a ser el del terminal destino, indicando a BioTime que lo sincronice ahí)."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                f"""INSERT INTO {self._tabla}
                        (employee_id, bio_index, bio_type, bio_no, bio_format,
                         major_ver, minor_ver, valid, duress, bio_tmp, sn,
                         update_time, status)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW(), 0)
                    ON CONFLICT (employee_id, bio_no, bio_index, bio_type, bio_format, major_ver, minor_ver, sn)
                    DO UPDATE SET bio_tmp = EXCLUDED.bio_tmp, valid = EXCLUDED.valid, update_time = NOW()""",
                employee_id, bio_index, bio_type, bio_no, bio_format,
                major_ver, minor_ver, valid, duress, bio_tmp, sn,
            )
