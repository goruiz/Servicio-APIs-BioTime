"""
Schemas de empleados de BioTime.
"""
from typing import Optional

from pydantic import BaseModel, Field


class EmployeeDto(BaseModel):
    """DTO de empleado desde BioTime."""

    id: int = Field(..., description="ID del empleado")
    emp_code: str = Field(..., description="Código del empleado")
    first_name: str = Field(..., description="Nombre del empleado")
    last_name: str = Field(..., description="Apellido del empleado")
    department: Optional[int] = Field(None, description="ID del departamento")
    position: Optional[int] = Field(None, description="ID de la posición")
    hire_date: Optional[str] = Field(None, description="Fecha de contratación")

    class Config:
        """Configuración del modelo."""
        json_schema_extra = {
            "example": {
                "id": 1,
                "emp_code": "EMP001",
                "first_name": "Juan",
                "last_name": "Pérez",
                "department": 1,
                "position": 2,
                "hire_date": "2024-01-15",
            }
        }
