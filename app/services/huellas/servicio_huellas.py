"""
Servicio de huellas dactilares.
Obtiene los datos directamente desde la base de datos PostgreSQL de BioTime,
ya que la API REST de BioTime no expone un endpoint para templates biométricos.
"""
from app.db.repositorios.repositorio_huellas import RepositorioHuellas
from app.interfaces.huellas.interface_huellas import IHuellas
from app.schemas.biotime.common import PaginatedResponse
from app.schemas.huellas.respuesta_huellas import HuellaDto


class ServicioHuellas(IHuellas):

    def __init__(self, repositorio: RepositorioHuellas) -> None:
        self._repositorio = repositorio

    async def obtener_huellas(self, page: int = 1, page_size: int = 10) -> PaginatedResponse[HuellaDto]:
        total, filas = await self._repositorio.obtener_huellas(page=page, page_size=page_size)
        huellas = [HuellaDto(**fila) for fila in filas]
        print(f"[Huellas] Obtenidas {len(huellas)}/{total} — página {page}")
        return PaginatedResponse[HuellaDto](count=total, next=None, previous=None, data=huellas)

    async def obtener_huellas_por_empleado(
        self, empleado_id: int, page: int = 1, page_size: int = 10
    ) -> PaginatedResponse[HuellaDto]:
        total, filas = await self._repositorio.obtener_huellas_por_empleado(
            empleado_id=empleado_id, page=page, page_size=page_size
        )
        huellas = [HuellaDto(**fila) for fila in filas]
        print(f"[Huellas] Obtenidas {len(huellas)}/{total} — empleado ID={empleado_id}")
        return PaginatedResponse[HuellaDto](count=total, next=None, previous=None, data=huellas)
