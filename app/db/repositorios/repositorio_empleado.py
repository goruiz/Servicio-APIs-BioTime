"""
Repositorio de empleados.
Ejecuta queries SQL directamente sobre la tabla personnel_employee de BioTime
para campos que la API REST no permite escribir (ej: card_no).
"""
from typing import Optional

import asyncpg


class RepositorioEmpleado:

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def actualizar_campos_bd(
        self,
        empleado_id: int,
        card_no: Optional[str] = None,
        device_password: Optional[str] = None,
    ) -> None:
        """Actualiza card_no y/o device_password directamente en PostgreSQL
        (campos no aceptados por la API REST de BioTime)."""
        sets = []
        valores = []
        if card_no is not None:
            valores.append(card_no)
            sets.append(f"card_no = ${len(valores)}")
        if device_password is not None:
            valores.append(device_password)
            sets.append(f"device_password = ${len(valores)}")
        if not sets:
            return
        valores.append(empleado_id)
        async with self._pool.acquire() as conn:
            await conn.execute(
                f"UPDATE personnel_employee SET {', '.join(sets)} WHERE id = ${len(valores)}",
                *valores,
            )
