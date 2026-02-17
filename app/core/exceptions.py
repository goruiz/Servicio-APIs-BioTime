"""
Excepciones personalizadas de la aplicación.
"""


class BioTimeException(Exception):
    """Excepción base para errores relacionados con BioTime."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class BioTimeAuthenticationError(BioTimeException):
    """Error de autenticación con BioTime."""

    def __init__(self, message: str = "Error de autenticación con BioTime"):
        super().__init__(message, status_code=401)


class BioTimeConnectionError(BioTimeException):
    """Error de conexión con BioTime."""

    def __init__(self, message: str = "Error al conectar con BioTime"):
        super().__init__(message, status_code=502)


class BioTimeNotFoundError(BioTimeException):
    """Recurso no encontrado en BioTime."""

    def __init__(self, message: str = "Recurso no encontrado"):
        super().__init__(message, status_code=404)


class BioTimeValidationError(BioTimeException):
    """Error de validación de datos."""

    def __init__(self, message: str = "Datos inválidos"):
        super().__init__(message, status_code=422)
