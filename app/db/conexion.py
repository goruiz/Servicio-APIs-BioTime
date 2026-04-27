"""
Gestión del pool de conexiones a PostgreSQL.
El pool se inicia al arrancar la aplicación y se cierra al apagarla.
"""
import asyncpg

from app.core.config import settings

_pool: asyncpg.Pool | None = None


async def _migrar_constraint_biodata(pool: asyncpg.Pool) -> None:
    """
    Asegura que el constraint único de iclock_biodata incluya sn para permitir
    un registro por empleado+dedo por terminal. Si el constraint actual no incluye
    sn, lo recrea incluyéndolo.
    """
    tabla = settings.DB_TABLA_HUELLAS
    async with pool.acquire() as conn:
        fila = await conn.fetchrow(
            """
            SELECT conname, pg_get_constraintdef(oid) AS def
            FROM pg_constraint
            WHERE conrelid = $1::regclass
              AND contype = 'u'
              AND pg_get_constraintdef(oid) LIKE '%employee_id%bio_no%bio_index%'
            LIMIT 1
            """,
            tabla,
        )
        if not fila:
            print(f"[DB] AVISO - No se encontró constraint único en {tabla}, se omite migración")
            return

        if "sn" in fila["def"]:
            # print(f"[DB] Constraint de {tabla} ya incluye sn, no requiere migración")
            return

        nombre = fila["conname"]
        print(f"[DB] Migrando constraint '{nombre}' en {tabla} para incluir sn...")
        await conn.execute(f"ALTER TABLE {tabla} DROP CONSTRAINT {nombre}")
        await conn.execute(
            f"""ALTER TABLE {tabla}
                ADD CONSTRAINT {nombre}
                UNIQUE (employee_id, bio_no, bio_index, bio_type, bio_format, major_ver, minor_ver, sn)"""
        )
        print(f"[DB] Constraint '{nombre}' migrado exitosamente")


async def iniciar_conexion_bd() -> None:
    """Crea el pool de conexiones a PostgreSQL y aplica migraciones necesarias."""
    global _pool
    _pool = await asyncpg.create_pool(
        host=settings.DB_HOST,
        port=settings.DB_PUERTO,
        database=settings.DB_NOMBRE,
        user=settings.DB_USUARIO,
        password=settings.DB_PASSWORD,
        min_size=2,
        max_size=10,
    )
    await _migrar_constraint_biodata(_pool)


async def cerrar_conexion_bd() -> None:
    """Cierra el pool de conexiones. Llamar en el shutdown de FastAPI."""
    global _pool
    if _pool:
        await _pool.close()


def obtener_pool() -> asyncpg.Pool:
    """Devuelve el pool activo. Lanza error si no fue inicializado."""
    if _pool is None:
        raise RuntimeError("El pool de PostgreSQL no está inicializado")
    return _pool
