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
    PORT: int = 8001
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
    DB_TABLA_HUELLAS: str = Field(default="iclock_biodata", description="Tabla de huellas dactilares en BioTime")

    # Logging
    LOG_LEVEL: str = "INFO"

    # Scheduler de tareas
    TAREAS_HABILITADO: bool = Field(default=True, description="Habilita el polling periódico de tareas de Preciso")
    TAREAS_INTERVALO_SEGUNDOS: int = Field(default=60, description="Intervalo en segundos entre cada consulta de tareas")
    TAREAS_IPS_PERMITIR: List[str] = Field(default_factory=list, description="Si no está vacío, solo se procesan tareas cuya IP esté en esta lista")
    TAREAS_IPS_IGNORAR: List[str] = Field(default_factory=list, description="Si no está vacío, se omiten las tareas cuya IP esté en esta lista")
    UNICAMENTE_LEER_TAREAS: bool = Field(default=False, description="Si es True, el servicio solo leerá las tareas pero no las ejecutará. Útil para entornos de desarrollo o pruebas.")

    # Valores por defecto para empleados creados desde tareas Preciso (EMPDAT)
    # BioTime exige company, department y area; Preciso no los envía en el detalle de la tarea
    BIOTIME_DEFAULT_COMPANY_ID: int = Field(default=1, description="ID de la compañía por defecto en BioTime")
    BIOTIME_DEFAULT_DEPARTMENT_ID: int = Field(default=1, description="ID del departamento por defecto en BioTime")
    BIOTIME_DEFAULT_AREA_ID: int = Field(default=1, description="ID del área por defecto en BioTime")

    # Preciso API (para leer y completar tareas)
    PRECISO_BASE_URL: str = Field(default="", description="URL base del servidor Preciso (ej: http://192.168.1.10/)")
    PRECISO_USERNAME: str = Field(default="", description="Usuario OAuth2 de Preciso")
    PRECISO_PASSWORD: str = Field(default="", description="Contraseña OAuth2 de Preciso")
    PRECISO_CLIENT_ID: str = Field(default="", description="client_id de Laravel Passport en Preciso")
    PRECISO_CLIENT_SECRET: str = Field(default="", description="client_secret de Laravel Passport en Preciso")
    PRECISO_TIMEOUT: int = Field(default=30, description="Timeout en segundos para peticiones a Preciso")

    # Notificaciones Telegram
    TELEGRAM_BOT_TOKEN: str = Field(default="", description="Token del bot de Telegram (vacío = notificaciones desactivadas)")
    TELEGRAM_CHAT_ID: str = Field(default="", description="Chat ID o canal de Telegram destino de las notificaciones")
    ENVIA_NOTIFICACIONES_TELEGRAM: bool = Field(default=False, description="Habilita el envío de notificaciones por Telegram")
    TAREAS_NOTIFICACION_COOLDOWN_SEGUNDOS: int = Field(default=1800, description="Tiempo mínimo, en segundos, que debe pasar antes de reintentar una tarea (instruccion+detalle) que falló, y antes de volver a notificar por Telegram si sigue fallando. Mientras dura el cooldown, la tarea se omite en cada ciclo de polling sin ejecutarse ni perderse — sigue pendiente en Preciso — y se reintenta automáticamente al cumplirse el plazo")


# Instancia global de configuración
settings = Settings()
