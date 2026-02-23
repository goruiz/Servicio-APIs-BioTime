"""
Configuración central de la aplicación.
El ambiente se selecciona con la variable de sistema ENVIRONMENT (default: local).
Carga .env como base y .env.{ENVIRONMENT} como override específico del ambiente.
"""
import os
from typing import List, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_AMBIENTE = os.getenv("ENVIRONMENT", "local")


class Settings(BaseSettings):
    """Configuración general de la aplicación."""

    model_config = SettingsConfigDict(
        env_file=(".env", f".env.{_AMBIENTE}"),  # .env.{ambiente} override .env
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Ambiente activo
    ENVIRONMENT: Literal["local", "desarrollo", "produccion"] = "local"

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

    # Configuración de BioTime API
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

    # Base de datos PostgreSQL (conexión directa para datos no expuestos por la API)
    DB_HOST: str = Field(default="127.0.0.1", description="Host de PostgreSQL")
    DB_PUERTO: int = Field(default=5432, description="Puerto de PostgreSQL")
    DB_NOMBRE: str = Field(default="biotime", description="Nombre de la base de datos")
    DB_USUARIO: str = Field(default="postgres", description="Usuario de PostgreSQL")
    DB_PASSWORD: str = Field(..., description="Contraseña de PostgreSQL")
    DB_TABLA_HUELLAS: str = Field(default="biodata_biotemplate", description="Tabla de huellas dactilares en BioTime")

    # Logging
    LOG_LEVEL: str = "INFO"


# Instancia global de configuración
settings = Settings()
