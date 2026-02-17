"""
Utilidades para manejo de peticiones HTTP.
"""
from typing import Dict, Optional


def build_query_params(
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    **kwargs,
) -> Dict[str, str]:
    """
    Construye diccionario de parámetros query eliminando valores None.

    Args:
        page: Número de página
        page_size: Tamaño de página
        **kwargs: Parámetros adicionales

    Returns:
        Diccionario con parámetros no nulos
    """
    params = {}

    if page is not None:
        params["page"] = str(page)

    if page_size is not None:
        params["page_size"] = str(page_size)

    # Agregar parámetros adicionales
    for key, value in kwargs.items():
        if value is not None:
            params[key] = str(value)

    return params
