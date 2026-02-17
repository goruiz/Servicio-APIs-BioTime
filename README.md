# Servicio APIs BioTime

Servicio de APIs REST para conectarse con BioTime, sistema de gestión biométrica de ZKTeco. Este proyecto proporciona una interfaz HTTP moderna y bien estructurada para interactuar con los biométricos y gestionar datos de personal.

## 📋 Características

- ✅ **Arquitectura Limpia**: Separación clara de responsabilidades siguiendo principios SOLID
- ✅ **FastAPI**: Framework moderno, rápido y asíncrono
- ✅ **Autenticación JWT**: Manejo automático de tokens con BioTime
- ✅ **Paginación**: Soporte completo para datos paginados
- ✅ **Logging Estructurado**: Logs JSON para producción, console para desarrollo
- ✅ **Validación de Datos**: Usando Pydantic v2
- ✅ **Inyección de Dependencias**: Facilita testing y mantenibilidad
- ✅ **Documentación Automática**: Swagger UI y ReDoc incluidos
- ✅ **Tipado Estático**: Type hints completos para mejor IDE support

## 🏗️ Arquitectura

```
app/
├── api/                    # Capa de presentación (Controllers/Routes)
│   ├── v1/routes/         # Endpoints versionados
│   └── dependencies.py    # Inyección de dependencias
├── core/                  # Configuración y utilidades core
│   ├── config.py         # Configuración centralizada
│   ├── logging.py        # Setup de logging
│   └── exceptions.py     # Excepciones personalizadas
├── schemas/              # DTOs/Modelos Pydantic
│   └── biotime/         # Schemas específicos de BioTime
├── services/            # Lógica de negocio
│   ├── interfaces/      # Contratos (SOLID - D)
│   └── implementations/ # Implementaciones concretas
├── clients/            # Clientes HTTP externos
└── utils/             # Utilidades compartidas
```

### Principios SOLID Aplicados

- **S**: Cada clase tiene una única responsabilidad
- **O**: Extensible mediante interfaces sin modificar código existente
- **L**: Las implementaciones son intercambiables con sus interfaces
- **I**: Interfaces específicas por funcionalidad
- **D**: Dependencias inyectadas, no acoplamiento directo

## 🚀 Inicio Rápido

### Prerrequisitos

- Python 3.12+
- pip o poetry
- BioTime API corriendo y accesible

### Instalación

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd Servicio-APIs-BioTime
```

2. **Crear entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus credenciales de BioTime
```

5. **Ejecutar la aplicación**
```bash
python -m app.main
# o
uvicorn app.main:app --reload
```

La aplicación estará disponible en: `http://localhost:8000`

- **Documentación Swagger**: `http://localhost:8000/api/v1/docs`
- **ReDoc**: `http://localhost:8000/api/v1/redoc`
- **Health Check**: `http://localhost:8000/health`

## 📝 Variables de Entorno

Crea un archivo `.env` basado en `.env.example`:

```env
# Aplicación
PROJECT_NAME=Servicio APIs BioTime
VERSION=1.0.0
DEBUG=True
HOST=0.0.0.0
PORT=8000

# BioTime API
BIOTIME_BASE_URL=http://localhost:8081/
BIOTIME_USERNAME=tu_usuario
BIOTIME_PASSWORD=tu_password
BIOTIME_TIMEOUT=30

# Logging
LOG_LEVEL=INFO
```

## 🔌 Endpoints Disponibles

### Empleados

#### `GET /api/v1/employees`
Obtiene lista paginada de empleados.

**Query Parameters:**
- `page` (int, default=1): Número de página
- `page_size` (int, default=10, max=100): Registros por página

**Response:**
```json
{
  "count": 100,
  "next": "http://api/employees/?page=2",
  "previous": null,
  "data": [
    {
      "id": 1,
      "emp_code": "EMP001",
      "first_name": "Juan",
      "last_name": "Pérez",
      "department": 1,
      "position": 2,
      "hire_date": "2024-01-15"
    }
  ]
}
```

## 🧪 Testing

```bash
# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# Ejecutar tests
pytest

# Con cobertura
pytest --cov=app --cov-report=html

# Tests específicos
pytest tests/unit/
pytest tests/integration/
```

## 🔧 Desarrollo

### Formateo de código

```bash
# Formatear con Black
black app/ tests/

# Ordenar imports
isort app/ tests/

# Linting
flake8 app/ tests/

# Type checking
mypy app/
```

### Estructura de un nuevo módulo

Para agregar un nuevo recurso (ej: Departamentos):

1. **Crear schemas** en `app/schemas/biotime/department.py`
2. **Crear interface** en `app/services/interfaces/department_service.py`
3. **Implementar servicio** en `app/services/implementations/department_service.py`
4. **Crear router** en `app/api/v1/routes/departments.py`
5. **Registrar router** en `app/api/v1/router.py`
6. **Agregar dependency** en `app/api/dependencies.py`

## 📚 Documentación Adicional

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [BioTime API Documentation](https://biotime-api-docs-url)

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📄 Licencia

[Especificar licencia]

## 👥 Autores

[Tu nombre/equipo]

---

**Nota**: Este es un servicio backend. Se espera que sea consumido por otra aplicación que maneje la lógica de presentación y flujos de usuario.
