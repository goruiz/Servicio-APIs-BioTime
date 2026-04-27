"""
Servicio de notificaciones por Telegram.

Requiere configurar TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID en el .env.
Si alguna de las dos variables está vacía, todas las llamadas a `notificar`
son no-operaciones silenciosas.
"""
from datetime import datetime

import httpx

from app.core.config import settings

_TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
_LIMITE_CHARS = 3800  # Telegram limita a 4096; dejamos margen para el encabezado


def _construir_mensaje(titulo: str, detalle: str) -> str:
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    lineas = [f"[{settings.PROJECT_NAME}]", titulo, timestamp]
    if detalle:
        lineas.append("")
        lineas.append(detalle[:_LIMITE_CHARS])
    return "\n".join(lineas)


async def notificar(titulo: str, detalle: str = "") -> None:
    """
    Envía un mensaje de texto al chat de Telegram configurado (versión async).

    Falla silenciosamente para no interrumpir el flujo de la aplicación.
    """
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        return

    url = _TELEGRAM_API.format(token=settings.TELEGRAM_BOT_TOKEN)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                url,
                json={
                    "chat_id": settings.TELEGRAM_CHAT_ID,
                    "text": _construir_mensaje(titulo, detalle),
                },
            )
    except Exception:
        pass


def notificar_sync(titulo: str, detalle: str = "") -> None:
    """
    Versión síncrona de notificar. Usar solo fuera de un event loop activo
    (por ejemplo, en bloques finally del __main__ tras el cierre de uvicorn).
    """
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        return

    url = _TELEGRAM_API.format(token=settings.TELEGRAM_BOT_TOKEN)
    try:
        with httpx.Client(timeout=10) as client:
            client.post(
                url,
                json={
                    "chat_id": settings.TELEGRAM_CHAT_ID,
                    "text": _construir_mensaje(titulo, detalle),
                },
            )
    except Exception:
        pass
