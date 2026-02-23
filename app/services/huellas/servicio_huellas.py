"""
Servicio de huellas dactilares.
Obtiene los datos directamente desde la base de datos PostgreSQL de BioTime,
ya que la API REST de BioTime no expone un endpoint para templates biométricos.
"""
from app.core.logging import get_logger
from app.db.repositorios.repositorio_huellas import RepositorioHuellas
from app.interfaces.huellas.interface_huellas import IHuellas
from app.schemas.biotime.common import PaginatedResponse
from app.schemas.huellas.respuesta_huellas import HuellaDto

logger = get_logger(__name__)


class ServicioHuellas(IHuellas):

    def __init__(self, repositorio: RepositorioHuellas) -> None:
        self._repositorio = repositorio

    async def obtener_huellas(
        self, page: int = 1, page_size: int = 10
    ) -> PaginatedResponse[HuellaDto]:
        logger.info("Obteniendo huellas desde BD", page=page, page_size=page_size)
        total, filas = await self._repositorio.obtener_huellas(page=page, page_size=page_size)
        huellas = [HuellaDto(**fila) for fila in filas]
        logger.info("Huellas obtenidas", total=total, returned=len(huellas))
        return PaginatedResponse[HuellaDto](
            count=total,
            next=None,
            previous=None,
            data=huellas,
        )

    async def obtener_huellas_por_empleado(
        self, codigo_empleado: str, page: int = 1, page_size: int = 10
    ) -> PaginatedResponse[HuellaDto]:
        logger.info("Obteniendo huellas por empleado desde BD", codigo_empleado=codigo_empleado, page=page, page_size=page_size)
        total, filas = await self._repositorio.obtener_huellas_por_empleado(
            codigo_empleado=codigo_empleado, page=page, page_size=page_size
        )
        huellas = [HuellaDto(**fila) for fila in filas]
        logger.info("Huellas por empleado obtenidas", codigo_empleado=codigo_empleado, total=total, returned=len(huellas))
        return PaginatedResponse[HuellaDto](
            count=total,
            next=None,
            previous=None,
            data=huellas,
        )
