"""
Schemas (DTOs) para el sistema de tareas de Preciso.
"""
from pydantic import BaseModel


class TareaDto(BaseModel):
    """Representa una tarea pendiente recibida desde la API de Preciso."""

    id_tarea: int
    ip: str
    instruccion: str
    detalle: str
    id_tabla: int


class CompletarTareaPayload(BaseModel):
    """Payload para marcar una tarea como completada en Preciso (POST /api/completar_tarea)."""

    model_config = {"extra": "allow"}

    id_tarea: int
    instruccion: str
    respuesta: str = "0"
