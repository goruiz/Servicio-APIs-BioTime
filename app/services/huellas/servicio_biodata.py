"""
Servicio de biodata (templates biométricos) vía API REST de BioTime.
Usado internamente por los manejadores de tareas (EMPHUE, DELHUE, COPHUE, REPHUE).
No tiene ruta HTTP propia porque la API REST de BioTime no lo expone como recurso público.
"""
from app.clients.biotime_client import BioTimeClient


class ServicioBiodata:
    """Acceso a iclock/api/biodata/ de BioTime para operaciones de templates biométricos."""

    def __init__(self, client: BioTimeClient) -> None:
        self._client = client

    async def obtener_templates_por_emp_code(self, emp_code: str) -> list[str]:
        """Devuelve los templates biométricos (bio_data) de un empleado, paginando internamente."""
        templates: list[str] = []
        page = 1
        while True:
            data = await self._client.get(
                "iclock/api/biodata/", params={"emp_code": emp_code, "page": page, "page_size": 50}
            )
            for registro in data.get("data", []):
                bio_data = registro.get("bio_data") or registro.get("biodata") or ""
                if bio_data:
                    templates.append(bio_data)
            if not data.get("next"):
                break
            page += 1
        print(f"[Biodata] Obtenidos {len(templates)} templates — emp_code={emp_code}")
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
