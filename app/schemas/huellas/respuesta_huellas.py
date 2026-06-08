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


class EstadoHuellasEmpleadoResponse(BaseDto):
    """Indica si un empleado tiene huellas registradas y en qué terminales."""

    emp_code: str = Field(..., description="Código del empleado en BioTime")
    tiene_huellas: bool = Field(..., description="True si el empleado tiene al menos una huella registrada")
    terminales: list[str] = Field(..., description="Números de serie de los terminales donde tiene huella")


class SincronizarTerminalesRequest(BaseDto):
    """Cuerpo de la petición para sincronizar huellas de un terminal origen a uno o varios destinos."""

    sn_origen: str = Field(..., description="Número de serie del terminal de origen")
    sns_destino: list[str] = Field(..., min_length=1, description="Números de serie de los terminales destino")


class ResultadoSincronizacionTerminal(BaseDto):
    """Resultado de la sincronización hacia un terminal destino específico."""

    sn_destino: str = Field(..., description="Número de serie del terminal destino")
    huellas_copiadas: int = Field(..., description="Huellas nuevas insertadas (sin contar las ya existentes)")
    sincronizado: bool = Field(..., description="Si el conteo en destino coincide con el origen tras la operación")


class SincronizarTerminalesResponse(BaseDto):
    """Resultado de la operación de sincronización entre terminales."""

    sn_origen: str = Field(..., description="Número de serie del terminal origen")
    total_huellas_origen: int = Field(..., description="Total de huellas en el terminal origen")
    terminales: list[ResultadoSincronizacionTerminal] = Field(..., description="Resultado por cada terminal destino")


class CopiarHuellaRequest(BaseDto):
    """Cuerpo de la petición para copiar huellas de un empleado a uno o varios terminales."""

    emp_code: str = Field(..., description="Código del empleado en BioTime")
    terminal_ips: list[str] = Field(..., min_length=1, description="IPs de los terminales destino")


class ResultadoTerminal(BaseDto):
    """Resultado de la copia a un terminal específico."""

    terminal_ip: str = Field(..., description="IP del terminal")
    terminal_sn: str = Field(..., description="Número de serie del terminal")
    templates_registrados: int = Field(..., description="Cantidad de templates enviados")


class CopiarHuellaResponse(BaseDto):
    """Resultado de la operación de copia de huellas a uno o varios terminales."""

    emp_code: str = Field(..., description="Código del empleado")
    terminales: list[ResultadoTerminal] = Field(..., description="Resultado por cada terminal")


class EnviarHuellasRequest(BaseDto):
    """Cuerpo opcional de la petición para enviar huellas a terminales."""

    sns: list[str] | None = Field(None, description="SNs de los terminales destino. Si se omite, se procesan todos los terminales con sensor de huella.")


class ResultadoEnvioTerminal(BaseDto):
    """Resultado del envío de comandos FINGERTMP a un terminal."""

    sn: str = Field(..., description="Número de serie del terminal")
    alias: str = Field(..., description="Nombre del terminal en BioTime")
    comandos_encolados: int = Field(..., description="Cantidad de comandos DATA UPDATE FINGERTMP encolados")


class EnviarHuellasResponse(BaseDto):
    """Resultado del envío masivo de huellas a terminales biométricos."""

    total_comandos: int = Field(..., description="Total de comandos encolados en todos los terminales")
    terminales: list[ResultadoEnvioTerminal] = Field(..., description="Detalle por terminal")
