"""
Schemas de autenticación para BioTime.
"""
from pydantic import Field

from app.schemas.base import BaseDto


class LoginRequest(BaseDto):
    """Request para login en BioTime."""

    username: str = Field(..., description="Usuario de BioTime")
    password: str = Field(..., description="Contraseña de BioTime")


class LoginResponse(BaseDto):
    """Response de login desde BioTime."""

    token: str = Field(..., description="Token JWT de autenticación")
