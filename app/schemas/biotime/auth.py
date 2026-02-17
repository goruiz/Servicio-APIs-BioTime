"""
Schemas de autenticación para BioTime.
"""
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Request para login en BioTime."""

    username: str = Field(..., description="Usuario de BioTime")
    password: str = Field(..., description="Contraseña de BioTime")


class LoginResponse(BaseModel):
    """Response de login desde BioTime."""

    token: str = Field(..., description="Token JWT de autenticación")
