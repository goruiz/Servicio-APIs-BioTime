"""
Schemas de empleados de BioTime.
"""
from typing import Optional, Union

from pydantic import BaseModel, Field, field_validator


class DepartmentDto(BaseModel):
    """DTO de departamento anidado en empleado."""

    id: int
    dept_code: str = ""
    dept_name: str = ""


class PositionDto(BaseModel):
    """DTO de posición anidada en empleado."""

    id: int
    position_code: str = ""
    position_name: str = ""


class EmployeeDto(BaseModel):
    """DTO de empleado desde BioTime."""

    id: int = Field(..., description="ID del empleado")
    emp_code: str = Field(..., description="Código del empleado")
    first_name: str = Field(..., description="Nombre del empleado")
    last_name: Optional[str] = Field(None, description="Apellido del empleado")
    department: Optional[Union[DepartmentDto, int]] = Field(None, description="Departamento del empleado")
    position: Optional[Union[PositionDto, int]] = Field(None, description="Posición del empleado")
    hire_date: Optional[str] = Field(None, description="Fecha de contratación")

    class Config:
        """Configuración del modelo."""
        json_schema_extra = {
            "example": {
                "id": 1,
                "emp_code": "EMP001",
                "first_name": "Juan",
                "last_name": "Pérez",
                "department": {"id": 1, "dept_code": "IT", "dept_name": "Tecnología"},
                "position": {"id": 2, "position_code": "DEV", "position_name": "Desarrollador"},
                "hire_date": "2024-01-15",
            }
        }
