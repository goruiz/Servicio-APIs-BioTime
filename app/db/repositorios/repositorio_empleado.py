"""
Repositorio de empleados.
Ejecuta queries SQL directamente sobre la tabla personnel_employee de BioTime
para campos que la API REST no permite escribir (ej: card_no), y para
diagnosticar rechazos de BioTime (card_no duplicado, department/area inexistente).
"""
from typing import Optional

import asyncpg


class RepositorioEmpleado:

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def buscar_por_card_no(self, card_no: str) -> Optional[dict]:
        """Retorna el empleado (id, emp_code, first_name, last_name) que actualmente
        tiene asignado ese card_no en BioTime, o None si ninguno lo tiene."""
        async with self._pool.acquire() as conn:
            fila = await conn.fetchrow(
                "SELECT id, emp_code, first_name, last_name FROM personnel_employee WHERE card_no = $1",
                card_no,
            )
            return dict(fila) if fila else None

    async def nombre_departamento(self, department_id: int) -> Optional[str]:
        """Retorna el nombre del departamento si existe en BioTime, o None si no."""
        async with self._pool.acquire() as conn:
            fila = await conn.fetchrow(
                "SELECT dept_name FROM personnel_department WHERE id = $1", department_id
            )
            return fila["dept_name"] if fila else None

    async def areas_inexistentes(self, area_ids: list[int]) -> list[int]:
        """Retorna los IDs de `area_ids` que NO existen en BioTime."""
        if not area_ids:
            return []
        async with self._pool.acquire() as conn:
            filas = await conn.fetch(
                "SELECT id FROM personnel_area WHERE id = ANY($1::int[])", area_ids
            )
            existentes = {f["id"] for f in filas}
            return [a for a in area_ids if a not in existentes]

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
