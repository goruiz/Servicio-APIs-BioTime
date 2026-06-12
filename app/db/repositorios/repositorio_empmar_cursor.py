"""
Repositorio del cursor de EMPMAR por terminal.
Guarda la última punch_time procesada por terminal para que cada ejecución
de EMPMAR solo consulte marcaciones nuevas.
"""
import asyncpg


class RepositorioEmpmarCursor:

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def obtener_cursor(self, terminal_sn: str) -> str | None:
        """Devuelve la última punch_time procesada para el terminal, o None si nunca se procesó."""
        async with self._pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT ultima_punch_time FROM servicio_empmar_cursor WHERE terminal_sn = $1",
                terminal_sn,
            )

    async def actualizar_cursor(self, terminal_sn: str, ultima_punch_time: str) -> None:
        """Guarda o actualiza la última punch_time procesada para el terminal."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO servicio_empmar_cursor (terminal_sn, ultima_punch_time)
                   VALUES ($1, $2)
                   ON CONFLICT (terminal_sn) DO UPDATE SET ultima_punch_time = EXCLUDED.ultima_punch_time""",
                terminal_sn,
                ultima_punch_time,
            )
