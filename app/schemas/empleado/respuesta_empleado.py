"""
Schemas de empleados de BioTime.
"""
from typing import List, Optional, Union

from pydantic import ConfigDict, Field

from app.schemas.base import BaseDto


class DepartmentDto(BaseDto):
    """DTO de departamento anidado en empleado."""

    id: int
    dept_code: str = ""
    dept_name: str = ""


class PositionDto(BaseDto):
    """DTO de posición anidada en empleado."""

    id: int
    position_code: str = ""
    position_name: str = ""


class EmpleadoCreateUpdateDto(BaseDto):
    """DTO para crear o actualizar un empleado en BioTime."""

    emp_code: str = Field(..., description="Código único del empleado")
    first_name: str = Field(..., description="Nombre del empleado")
    last_name: str = Field(..., description="Apellido del empleado")
    department: Optional[int] = Field(None, description="ID del departamento en BioTime")
    position: Optional[int] = Field(None, description="ID del cargo/posición en BioTime")
    area: List[int] = Field(default_factory=list, description="Lista de IDs de áreas (puede ser vacía)")
    hire_date: Optional[str] = Field(None, description="Fecha de contratación (YYYY-MM-DD)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "empCode": "EMP001",
                "firstName": "Juan",
                "lastName": "Pérez",
                "department": 1,
                "position": 2,
                "area": [],
                "hireDate": "2024-01-15",
            }
        }
    )


class EmployeeDto(BaseDto):
    """DTO de empleado desde BioTime."""

    id: int = Field(..., description="ID del empleado")
    emp_code: str = Field(..., description="Código del empleado")
    first_name: str = Field(..., description="Nombre del empleado")
    last_name: Optional[str] = Field(None, description="Apellido del empleado")
    department: Optional[Union[DepartmentDto, int]] = Field(None, description="Departamento del empleado")
    position: Optional[Union[PositionDto, int]] = Field(None, description="Posición del empleado")
    hire_date: Optional[str] = Field(None, description="Fecha de contratación")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "empCode": "EMP001",
                "firstName": "Juan",
                "lastName": "Pérez",
                "department": {"id": 1, "deptCode": "IT", "deptName": "Tecnología"},
                "position": {"id": 2, "positionCode": "DEV", "positionName": "Desarrollador"},
                "hireDate": "2024-01-15",
            }
        }
    )
