"""
Clase base de ruta para controlar el formato de serialización de respuestas.
Permite configurar globalmente si las respuestas JSON usan camelCase o snake_case
mediante la variable de entorno API_RESPONSE_CASE.
"""
from fastapi.routing import APIRoute

from app.core.config import settings


class ConfigurableAliasRoute(APIRoute):
    """
    APIRoute que lee API_RESPONSE_CASE al arrancar y aplica el formato correspondiente
    a todas las respuestas serializadas por Pydantic.

    - API_RESPONSE_CASE=camel  → response_model_by_alias=True  → claves en camelCase
    - API_RESPONSE_CASE=snake  → response_model_by_alias=False → claves en snake_case
    """

    def __init__(self, *args, **kwargs) -> None:
        kwargs["response_model_by_alias"] = settings.API_RESPONSE_CASE == "camel"
        super().__init__(*args, **kwargs)
