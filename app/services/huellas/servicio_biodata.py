"""
Servicio de biodata (templates biométricos) vía API REST de BioTime.
Usado internamente por los manejadores de tareas (EMPHUE, DELHUE, COPHUE, REPHUE).
No tiene ruta HTTP propia porque la API REST de BioTime no lo expone como recurso público.

Lectura de templates (EMPHUE): usa PostgreSQL directo (iclock_biodata), ya que el endpoint
iclock/api/biodata/ no existe en todas las versiones de BioTime.
Escritura/borrado (COPHUE, REPHUE, DELHUE): usa la API REST de BioTime.
"""
import asyncpg

from app.clients.biotime_client import BioTimeClient
from app.db.repositorios.repositorio_huellas import RepositorioHuellas
from app.services.empleado.servicio_empleado import ServicioEmpleado


class ServicioBiodata:
    """Acceso a templates biométricos: lectura vía PostgreSQL, escritura/borrado vía BioTime REST."""

    def __init__(self, client: BioTimeClient, pool: asyncpg.Pool) -> None:
        self._client = client
        self._pool = pool

    async def obtener_templates_por_emp_code(self, emp_code: str) -> list[str]:
        """Devuelve los bio_tmp de un empleado consultando PostgreSQL directamente."""
        empleado = await ServicioEmpleado(self._client).buscar_por_emp_code(emp_code)
        if not empleado:
            print(f"[Biodata] emp_code={emp_code} no encontrado en BioTime")
            return []
        repositorio = RepositorioHuellas(self._pool)
        templates = await repositorio.obtener_templates_por_empleado(empleado.id)
        print(f"[Biodata] Obtenidos {len(templates)} templates — emp_code={emp_code} (employee_id={empleado.id})")
        return templates

    async def eliminar_por_emp_code(self, emp_code: str) -> None:
        """Elimina todos los templates biométricos de un empleado en BioTime."""
        await self._client.delete("iclock/api/biodata/", params={"emp_code": emp_code})
        print(f"[Biodata] Eliminados templates — emp_code={emp_code}")

    async def registrar_template(self, emp_code: str, bio_data: str, terminal_sn: str) -> None:
        """Registra un template biométrico en un terminal de BioTime."""
        await self._client.post(
            "iclock/api/biodata/",
            json={"emp_code": emp_code, "bio_data": bio_data, "terminal_sn": terminal_sn},
        )
        print(f"[Biodata] Template registrado — emp_code={emp_code} SN={terminal_sn}")
