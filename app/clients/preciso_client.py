"""
Cliente HTTP para comunicarse con la API de Preciso.
Maneja autenticación OAuth2 (Laravel Passport) automáticamente.
Expone: obtener_tareas() y completar_tarea().
"""
from typing import Any, Optional

import httpx

from app.core.config import settings
from app.schemas.tareas.tarea import CompletarTareaPayload, TareaDto


class PrecisoAuthenticationError(Exception):
    """Error de autenticación con la API de Preciso."""


class PrecisoConnectionError(Exception):
    """Error de conexión o respuesta inesperada de la API de Preciso."""


class PrecisoClient:
    """
    Cliente para interactuar con la API de Preciso.

    Autentica usando OAuth2 password grant (Laravel Passport) y
    renueva el token automáticamente ante respuestas 401.
    """

    def __init__(self) -> None:
        self._token: Optional[str] = None
        self._base_url = settings.PRECISO_BASE_URL.rstrip("/") + "/"
        self._timeout = settings.PRECISO_TIMEOUT

    async def _login(self) -> str:
        """Obtiene un access token de Preciso via OAuth2 password grant."""
        payload = {
            "grant_type": "password",
            "client_id": settings.PRECISO_CLIENT_ID,
            "client_secret": settings.PRECISO_CLIENT_SECRET,
            "username": settings.PRECISO_USERNAME,
            "password": settings.PRECISO_PASSWORD,
            "scope": "",
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}oauth/token",
                    json=payload,
                )
                if response.status_code != 200:
                    print(f"[Preciso] ERROR - Login fallido: HTTP {response.status_code} — {response.text[:300]}")
                    raise PrecisoAuthenticationError(
                        f"Error de autenticación con Preciso: {response.status_code}"
                    )
                data = response.json()
                self._token = data["access_token"]
                return self._token
        except httpx.RequestError as e:
            print(f"[Preciso] ERROR - Sin conexión: {e}")
            raise PrecisoConnectionError(f"Error de conexión con Preciso: {str(e)}")

    async def _get_headers(self) -> dict:
        """Retorna headers de autenticación, realizando login si no hay token."""
        if not self._token:
            await self._login()
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json: Optional[Any] = None,
    ) -> dict:
        """
        Realiza una petición HTTP autenticada a Preciso con reintento en 401.
        """
        url = f"{self._base_url}{endpoint}"
        try:
            headers = await self._get_headers()
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.request(
                    method, url, headers=headers, params=params, json=json
                )

                # Token expirado: renovar y reintentar una vez
                if response.status_code == 401:
                    print(f"[Preciso] Token expirado, renovando...")
                    self._token = None
                    headers = await self._get_headers()
                    response = await client.request(
                        method, url, headers=headers, params=params, json=json
                    )

                response.raise_for_status()

                if response.status_code == 204 or not response.text.strip():
                    return {}

                return response.json()

        except httpx.HTTPStatusError as e:
            print(f"[Preciso] ERROR - HTTP {e.response.status_code} en {method} {endpoint} — {e.response.text[:300]}")
            raise PrecisoConnectionError(
                f"Error HTTP {e.response.status_code} en Preciso: {e.response.text[:300]}"
            )
        except httpx.RequestError as e:
            print(f"[Preciso] ERROR - Sin conexión en {method} {endpoint}: {e}")
            raise PrecisoConnectionError(f"Error de conexión con Preciso: {str(e)}")

    # ------------------------------------------------------------------
    # Operaciones públicas
    # ------------------------------------------------------------------

    async def obtener_tareas(self) -> list[TareaDto]:
        """GET /api/tareas → {"tareas": [...]}"""
        data = await self._request("GET", "api/tareas")
        tareas_raw = data.get("tareas", [])
        return [TareaDto(**t) for t in tareas_raw]

    async def completar_tarea(self, payload: CompletarTareaPayload) -> dict:
        """POST /api/completar_tarea"""
        return await self._request(
            "POST",
            "api/completar_tarea",
            json=payload.model_dump(),
        )
