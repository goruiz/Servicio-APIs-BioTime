"""
Schemas de empleados de BioTime.
"""
from typing import Optional, Union

from app.schemas.empleado.respuesta_empleado import EmployeeDto
from pydantic import BaseModel, ConfigDict, Field



class PositionDto(BaseModel):
    """DTO de posición anidada en empleado."""

    id: int
    position_code: str = ""
    position_name: str = ""


class MarcacionesDto(BaseModel):
    """DTO de marcaciones desde BioTime."""

    id: int = Field(..., description="ID de la marcación")
    emp_code: str = Field(..., description="Código del empleado")
    punch_time: str = Field(..., description="Fecha y hora de la marcación")
    punch_state: str = Field(..., description="Estado de la marcación")
    verify_type: int = Field(..., description="Tipo de verificación")
    work_code: Optional[str] = Field(None, description="Código de trabajo")
    terminal_sn: str = Field(..., description="Número de serie del terminal")
    terminal_alias: Optional[str] = Field(None, description="Alias del terminal")
    area_alias: Optional[str] = Field(None, description="Alias del área")
    longitude: Optional[float] = Field(None, description="Longitud GPS")
    latitude: Optional[float] = Field(None, description="Latitud GPS")
    gps_location: Optional[str] = Field(None, description="Ubicación GPS")
    mobile: Optional[str] = Field(None, description="Número de móvil")
    source: Optional[int] = Field(None, description="Fuente de la marcación")
    purpose: Optional[int] = Field(None, description="Propósito de la marcación")
    crc: Optional[str] = Field(None, description="CRC de la marcación")
    is_attendance: Optional[int] = Field(None, description="Indica si es una marcación de asistencia")
    reserved: Optional[str] = Field(None, description="Campo reservado")
    upload_time: str = Field(..., description="Fecha y hora de subida")
    sync_status: Optional[int] = Field(None, description="Estado de sincronización")
    sync_time: Optional[str] = Field(None, description="Fecha y hora de sincronización")
    emp: Optional[Union[int, EmployeeDto]] = Field(None, description="Información del empleado")
    terminal: Optional[PositionDto] = Field(None, description="Información del terminal")
 