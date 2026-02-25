"""
Cliente HTTP para comunicarse con la API de BioTime.
Maneja autenticación JWT automáticamente y expone operaciones CRUD completas.
"""
from typing import Any, Optional

import httpx

from app.core.config import settings
from app.core.exceptions import BioTimeAuthenticationError, BioTimeConnectionError
from app.schemas.biotime.auth import LoginRequest, LoginResponse


class BioTimeClient:
    """Cliente para interactuar con la API de BioTime."""

    def __init__(self):
        self._token: Optional[str] = None
        self._base_url = settings.BIOTIME_BASE_URL
        self._timeout = settings.BIOTIME_TIMEOUT

    async def _login(self) -> str:
        """Autentica contra BioTime y guarda el token JWT."""
        print(f"[BioTime] Login — {self._base_url} usuario={settings.BIOTIME_USERNAME}")
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
                    print(f"[BioTime] ERROR - Login fallido: HTTP {response.status_code} — {response.text[:200]}")
                    raise BioTimeAuthenticationError(
                        f"Error de autenticación: {response.status_code}"
                    )
                login_response = LoginResponse(**response.json())
                self._token = login_response.token
                return self._token
        except httpx.RequestError as e:
            print(f"[BioTime] ERROR - Sin conexión: {e}")
            raise BioTimeConnectionError(f"Error de conexión: {str(e)}")

    async def _get_headers(self) -> dict:
        """Retorna headers de autenticación, realizando login si no hay token."""
        if not self._token:
            await self._login()
        return {"Authorization": f"JWT {self._token}"}

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json: Optional[Any] = None,
    ) -> dict:
        """
        Realiza una petición HTTP autenticada a BioTime con reintentos en 401.

        Args:
            method: Método HTTP ('GET', 'POST', 'PUT', 'PATCH', 'DELETE')
            endpoint: Endpoint relativo (p.ej. 'personnel/api/employees/')
            params: Query parameters opcionales
            json: Cuerpo de la petición en formato JSON (para POST/PUT/PATCH)

        Returns:
            Respuesta JSON deserializada como dict (vacío si la respuesta es 204)

        Raises:
            BioTimeAuthenticationError: Si la autenticación falla
            BioTimeConnectionError: Si hay error de conexión o HTTP inesperado
        """
        try:
            headers = await self._get_headers()
            async with httpx.AsyncClient(
                base_url=self._base_url,
                headers=headers,
                timeout=self._timeout,
            ) as client:
                response = await client.request(
                    method, endpoint, params=params, json=json
                )

                # Token expirado: un solo reintento con token renovado
                if response.status_code == 401:
                    print(f"[BioTime] Token expirado, renovando...")
                    self._token = None
                    headers = await self._get_headers()

                async with httpx.AsyncClient(
                    base_url=self._base_url,
                    headers=headers,
                    timeout=self._timeout,
                ) as retry_client:
                    if response.status_code == 401:
                        response = await retry_client.request(
                            method, endpoint, params=params, json=json
                        )

                response.raise_for_status()

                # DELETE y algunos PATCH devuelven 204 sin cuerpo
                if response.status_code == 204:
                    return {}

                # BioTime puede devolver cuerpo vacío (ej: solo "\n") con status 200
                text = response.text.strip()
                if not text:
                    return {}

                try:
                    return response.json()
                except Exception:
                    print(f"[BioTime] ERROR - Respuesta no-JSON en {method} {endpoint}: {text[:200]}")
                    raise BioTimeConnectionError(
                        f"Respuesta inesperada de BioTime (no es JSON): {text[:200]}"
                    )

        except httpx.HTTPStatusError as e:
            print(f"[BioTime] ERROR - HTTP {e.response.status_code} en {method} {endpoint}")
            raise BioTimeConnectionError(
                f"Error HTTP {e.response.status_code}: {e.response.text}"
            )
        except httpx.RequestError as e:
            print(f"[BioTime] ERROR - Sin conexión en {method} {endpoint}: {e}")
            raise BioTimeConnectionError(f"Error de conexión: {str(e)}")

    # ------------------------------------------------------------------
    # Operaciones CRUD públicas
    # ------------------------------------------------------------------

    async def get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        return await self._request("GET", endpoint, params=params)

    async def post(self, endpoint: str, json: Any, params: Optional[dict] = None) -> dict:
        return await self._request("POST", endpoint, params=params, json=json)

    async def put(self, endpoint: str, json: Any, params: Optional[dict] = None) -> dict:
        return await self._request("PUT", endpoint, params=params, json=json)

    async def patch(self, endpoint: str, json: Any, params: Optional[dict] = None) -> dict:
        return await self._request("PATCH", endpoint, params=params, json=json)

    async def delete(self, endpoint: str, params: Optional[dict] = None) -> dict:
        return await self._request("DELETE", endpoint, params=params)
