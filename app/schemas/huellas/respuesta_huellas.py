"""
Schemas de huellas dactilares de BioTime.
"""
from typing import Optional, Union

from pydantic import Field

from app.schemas.base import BaseDto
from app.schemas.empleado.respuesta_empleado import EmployeeDto


class HuellaDto(BaseDto):
    """DTO de huella dactilar desde BioTime (personnel/api/userfingerprint/)."""

    id: int = Field(..., description="ID del registro de huella")
    emp_code: str = Field(..., description="Código del empleado")
    finger_id: int = Field(..., description="Índice del dedo (0-9)")
    valid: int = Field(..., description="Indica si la huella es válida (1=válida, 0=inválida)")
    template: Optional[str] = Field(None, description="Template de la huella (base64)")
    reuse: Optional[int] = Field(None, description="Flag de reutilización")
    emp: Optional[Union[int, EmployeeDto]] = Field(None, description="Referencia al empleado")
