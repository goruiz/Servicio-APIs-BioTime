"""
Configuración central de la aplicación.
Maneja variables de entorno y configuraciones globales.
"""
from typing import List, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración general de la aplicación."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Información del proyecto
    PROJECT_NAME: str = "Servicio APIs BioTime"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Configuración del servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"

    # CORS
    ALLOWED_ORIGINS: List[str] = Field(default_factory=lambda: ["*"])

    # Configuración de BioTime
    BIOTIME_BASE_URL: str = Field(..., description="URL base de BioTime API")
    BIOTIME_USERNAME: str = Field(..., description="Usuario de BioTime")
    BIOTIME_PASSWORD: str = Field(..., description="Contraseña de BioTime")
    BIOTIME_TIMEOUT: int = Field(default=30, description="Timeout en segundos")

    # Formato de respuesta JSON
    API_RESPONSE_CASE: Literal["camel", "snake"] = Field(
        default="camel",
        description="Formato de las claves en las respuestas JSON: 'camel' (empCode) o 'snake' (emp_code)",
    )

    # Sincronización de terminales biométricos
    BIOTIME_SYNC_HABILITADO: bool = Field(default=True, description="Habilita la sincronización automática tras operaciones de escritura")

    # Logging
    LOG_LEVEL: str = "INFO"


# Instancia global de configuración
settings = Settings()
