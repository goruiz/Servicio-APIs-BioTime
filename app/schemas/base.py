"""
Clase base para todos los schemas de la aplicación.
Centraliza la configuración de serialización: acepta tanto camelCase como snake_case.
Para deshabilitar esta normalización basta con cambiar aquí.
"""
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BaseDto(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,  # acepta camelCase (alias) Y snake_case (nombre de campo)
    )
