"""
Schemas de huellas dactilares de BioTime.
Mapeados desde la tabla iclock_biodata de PostgreSQL.
"""
from typing import Optional

from pydantic import Field

from app.schemas.base import BaseDto


class HuellaDto(BaseDto):
    """DTO de huella dactilar leído directamente desde iclock_biodata."""

    id: int = Field(..., description="ID del registro")
    employee_id: int = Field(..., description="ID del empleado (FK a personnel_employee.id)")
    bio_index: int = Field(..., description="Índice del dedo / elemento biométrico (0-9)")
    bio_type: int = Field(..., description="Tipo biométrico (1=huella, etc.)")
    bio_no: int = Field(..., description="Número de template biométrico")
    bio_format: int = Field(..., description="Formato del template")
    valid: int = Field(..., description="Indica si es válido (1=sí, 0=no)")
    duress: int = Field(..., description="Flag de coacción")
    bio_tmp: Optional[str] = Field(None, description="Template biométrico (base64)")
    sn: Optional[str] = Field(None, description="Número de serie del terminal de origen")
