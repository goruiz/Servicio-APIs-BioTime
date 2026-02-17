"""
Cliente HTTP para comunicarse con la API de BioTime.
Maneja autenticación y peticiones HTTP.
"""
from typing import Optional

import httpx

from app.core.config import settings
from app.core.exceptions import BioTimeAuthenticationError, BioTimeConnectionError
from app.core.logging import get_logger
from app.schemas.biotime.auth import LoginRequest, LoginResponse

logger = get_logger(__name__)


class BioTimeClient:
    """Cliente para interactuar con la API de BioTime."""

    def __init__(self):
        """Inicializa el cliente de BioTime."""
        self._token: Optional[str] = None
        self._base_url = settings.BIOTIME_BASE_URL
        self._timeout = settings.BIOTIME_TIMEOUT

    async def _login(self) -> str:
        """
        Realiza login en BioTime y obtiene el token JWT.

        Returns:
            Token JWT de autenticación

        Raises:
            BioTimeAuthenticationError: Si el login falla
            BioTimeConnectionError: Si hay error de conexión
        """
        logger.info("Autenticando contra BioTime...")

        login_data = LoginRequest(
            username=settings.BIOTIME_USERNAME,
            password=settings.BIOTIME_PASSWORD,
        )

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}jwt-api-token-auth/",
                    json=login_data.model_dump(),
                )

                if response.status_code != 200:
                    logger.error(
                        "Login fallido contra BioTime",
                        status_code=response.status_code,
                        body=response.text,
                    )
                    raise BioTimeAuthenticationError(
                        f"Error de autenticación: {response.status_code}"
                    )

                login_response = LoginResponse(**response.json())
                self._token = login_response.token
                logger.info("Autenticación exitosa contra BioTime")
                return self._token

        except httpx.RequestError as e:
            logger.error("Error de conexión con BioTime", error=str(e))
            raise BioTimeConnectionError(f"Error de conexión: {str(e)}")

    async def _get_authenticated_client(self) -> httpx.AsyncClient:
        """
        Obtiene un cliente HTTP autenticado.

        Returns:
            Cliente HTTP con headers de autenticación

        Raises:
            BioTimeAuthenticationError: Si el login falla
        """
        if not self._token:
            await self._login()

        headers = {"Authorization": f"JWT {self._token}"}
        return httpx.AsyncClient(
            base_url=self._base_url,
            headers=headers,
            timeout=self._timeout,
        )

    async def get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """
        Realiza una petición GET autenticada a BioTime.

        Args:
            endpoint: Endpoint de la API (sin base_url)
            params: Parámetros query opcionales

        Returns:
            Respuesta JSON deserializada

        Raises:
            BioTimeAuthenticationError: Si hay error de autenticación
            BioTimeConnectionError: Si hay error de conexión
        """
        try:
            client = await self._get_authenticated_client()
            async with client:
                response = await client.get(endpoint, params=params)

                # Si el token expiró, reintentar con nuevo token
                if response.status_code == 401:
                    logger.warning("Token expirado. Reintentando login...")
                    self._token = None
                    client = await self._get_authenticated_client()
                    async with client:
                        response = await client.get(endpoint, params=params)

                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(
                "Error HTTP en petición a BioTime",
                status_code=e.response.status_code,
                endpoint=endpoint,
            )
            raise BioTimeConnectionError(
                f"Error HTTP {e.response.status_code}: {e.response.text}"
            )
        except httpx.RequestError as e:
            logger.error("Error de conexión con BioTime", error=str(e), endpoint=endpoint)
            raise BioTimeConnectionError(f"Error de conexión: {str(e)}")
