"""
Schemas de terminales biométricos de BioTime.
"""
from typing import Optional

from pydantic import Field

from app.schemas.base import BaseDto


class TerminalDto(BaseDto):
    """DTO de terminal biométrico desde BioTime (iclock/api/terminals/)."""

    id: int = Field(..., description="ID del terminal en BioTime")
    sn: str = Field(..., description="Número de serie del dispositivo (coincide con terminal_sn en marcaciones)")
    alias: Optional[str] = Field(None, description="Nombre/alias del terminal")
    ip_address: Optional[str] = Field(None, description="Dirección IP del terminal")
    area_alias: Optional[str] = Field(None, description="Nombre del área donde está ubicado el terminal")
    firmware_ver: Optional[str] = Field(None, description="Versión del firmware del dispositivo")
    platform: Optional[str] = Field(None, description="Plataforma del dispositivo")
    push_version: Optional[str] = Field(None, description="Versión del protocolo push")
    sync_time: Optional[str] = Field(None, description="Última fecha/hora de sincronización")
    heartbeat: Optional[int] = Field(None, description="Intervalo de heartbeat en segundos")
    transfer_mode: Optional[int] = Field(None, description="Modo de transferencia de datos")
    is_reg: Optional[int] = Field(None, description="Indica si el terminal está registrado (1=sí, 0=no)")
