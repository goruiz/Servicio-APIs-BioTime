"""
Servicio de áreas de BioTime.
Obtiene los datos desde la API REST de BioTime (personnel/api/areas/).
"""
from app.clients.biotime_client import BioTimeClient
from app.interfaces.areas.interface_areas import IAreas
from app.schemas.areas.respuesta_areas import AreaDto
from app.schemas.biotime.common import PaginatedResponse


class ServicioAreas(IAreas):

    def __init__(self, client: BioTimeClient) -> None:
        self._client = client

    async def obtener_areas(self, page: int = 1, page_size: int = 10) -> PaginatedResponse[AreaDto]:
        params = {"page": page, "page_size": page_size}
        response_data = await self._client.get("personnel/api/areas/", params=params)
        areas = [AreaDto(**a) for a in response_data.get("data", [])]
        print(f"[Area] Obtenidas {len(areas)}/{response_data.get('count', 0)} — página {page}")
        return PaginatedResponse[AreaDto](
            count=response_data.get("count", 0),
            next=response_data.get("next"),
            previous=response_data.get("previous"),
            data=areas,
        )

    async def obtener_area_por_id(self, area_id: int) -> AreaDto:
        response_data = await self._client.get(f"personnel/api/areas/{area_id}/")
        area = AreaDto(**response_data)
        print(f"[Area] Obtenida — ID={area_id} area_code={area.area_code}")
        return area
