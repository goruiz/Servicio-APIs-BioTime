"""
Schemas de áreas de BioTime.
"""
from typing import Optional, Union

from pydantic import Field

from app.schemas.base import BaseDto


class AreaPadreDto(BaseDto):
    """DTO del área padre anidada en un área."""

    id: int
    area_code: str = ""
    area_name: str = ""


class AreaDto(BaseDto):
    """DTO de área desde BioTime (personnel/api/areas/)."""

    id: int = Field(..., description="ID del área en BioTime")
    area_code: str = Field(..., description="Código del área")
    area_name: str = Field(..., description="Nombre del área")
    parent_area: Optional[Union[AreaPadreDto, int]] = Field(None, description="Área padre (jerarquía)")
