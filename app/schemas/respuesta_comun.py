"""
Schemas de respuestas estándar de la API.
"""
from typing import Any, Optional

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Respuesta de error estándar."""

    error: str = Field(..., description="Mensaje de error")
    detail: Optional[str] = Field(None, description="Detalle adicional del error")
    status_code: int = Field(..., description="Código de estado HTTP")


class SuccessResponse(BaseModel):
    """Respuesta exitosa estándar."""

    message: str = Field(..., description="Mensaje de éxito")
    data: Optional[Any] = Field(None, description="Datos adicionales")
