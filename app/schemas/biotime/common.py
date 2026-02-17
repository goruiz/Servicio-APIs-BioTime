"""
Schemas comunes de BioTime.
"""
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Respuesta paginada genérica desde BioTime."""

    count: int = Field(..., description="Número total de registros")
    next: Optional[str] = Field(None, description="URL de la siguiente página")
    previous: Optional[str] = Field(None, description="URL de la página anterior")
    data: List[T] = Field(default_factory=list, description="Datos de la página actual")

    class Config:
        """Configuración del modelo."""
        json_schema_extra = {
            "example": {
                "count": 100,
                "next": "http://api.example.com/employees/?page=2",
                "previous": None,
                "data": [],
            }
        }
