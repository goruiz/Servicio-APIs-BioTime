"""
Schemas (DTOs) para el sistema de tareas de Preciso.
"""
from typing import Awaitable, Callable, Optional

from pydantic import BaseModel, Field


class TareaDto(BaseModel):
    """Representa una tarea pendiente recibida desde la API de Preciso."""

    id_tarea: int
    ip: str
    instruccion: str
    detalle: str
    id_tabla: int


class CompletarTarea(BaseModel):
    """Payload para marcar una tarea como completada en Preciso (POST /api/completar_tarea)."""

    model_config = {"extra": "allow", "arbitrary_types_allowed": True}

    id_tarea: int
    instruccion: str
    respuesta: str = "0"
    # Coroutine opcional que se ejecuta DESPUÉS de que Preciso confirma recepción.
    # No se serializa en el POST a Preciso.
    on_completado: Optional[Callable[[], Awaitable[None]]] = Field(default=None, exclude=True)
