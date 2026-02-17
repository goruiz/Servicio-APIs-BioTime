# Arquitectura del Proyecto

## Visión General

Este proyecto implementa un servicio de APIs REST para conectarse con BioTime siguiendo principios de **Clean Architecture** y **SOLID**.

## Capas de la Arquitectura

### 1. Capa de Presentación (`app/api/`)
**Responsabilidad**: Manejar peticiones HTTP y respuestas

- **`v1/routes/`**: Endpoints de la API
  - `employees.py`: CRUD de empleados
  - Futuros: `departments.py`, `positions.py`, etc.
- **`dependencies.py`**: Inyección de dependencias de FastAPI
- **`router.py`**: Enrutador principal que agrupa todos los routers

**Principios aplicados**:
- SRP: Cada router maneja un solo recurso
- DIP: Depende de interfaces, no implementaciones

### 2. Capa de Dominio (`app/schemas/`)
**Responsabilidad**: Definir estructuras de datos y contratos

- **`biotime/`**: Modelos específicos de BioTime
  - `auth.py`: LoginRequest, LoginResponse
  - `employee.py`: EmployeeDto
  - `common.py`: PaginatedResponse
- **`responses.py`**: Respuestas estándar de la API

**Principios aplicados**:
- SRP: Cada archivo agrupa schemas relacionados
- ISP: Modelos específicos para cada caso de uso

### 3. Capa de Aplicación (`app/services/`)
**Responsabilidad**: Lógica de negocio y orquestación

- **`interfaces/`**: Contratos de servicios
  - `biotime_service.py`: IBioTimeService (interfaz)
- **`implementations/`**: Implementaciones concretas
  - `biotime_service.py`: BioTimeService (implementación)

**Principios aplicados**:
- OCP: Abierto a extensión mediante nuevas implementaciones
- LSP: Las implementaciones son intercambiables
- DIP: Depende de abstracciones (IBioTimeService)

### 4. Capa de Infraestructura (`app/clients/`)
**Responsabilidad**: Comunicación con servicios externos

- **`biotime_client.py`**: Cliente HTTP para BioTime
  - Manejo de autenticación JWT
  - Reintentos automáticos en caso de token expirado
  - Manejo de errores HTTP

**Principios aplicados**:
- SRP: Solo se encarga de comunicación HTTP
- OCP: Fácil de extender para nuevos endpoints

### 5. Capa Core (`app/core/`)
**Responsabilidad**: Configuración y utilidades transversales

- **`config.py`**: Configuración centralizada usando Pydantic Settings
- **`logging.py`**: Setup de logging estructurado
- **`exceptions.py`**: Excepciones personalizadas del dominio

### 6. Utilidades (`app/utils/`)
**Responsabilidad**: Funciones helper reutilizables

- **`http_helpers.py`**: Helpers para peticiones HTTP

## Flujo de Datos

```
HTTP Request
    ↓
[API Router] (app/api/v1/routes/employees.py)
    ↓ (dependency injection)
[Service Interface] (app/services/interfaces/biotime_service.py)
    ↓ (implementation)
[Service] (app/services/implementations/biotime_service.py)
    ↓ (HTTP call)
[Client] (app/clients/biotime_client.py)
    ↓
[BioTime API]
    ↓
[Response]
    ↓ (parsing to DTOs)
[Pydantic Models] (app/schemas/biotime/)
    ↓
HTTP Response
```

## Principios SOLID en Acción

### Single Responsibility Principle (SRP)
- Cada clase tiene una única razón para cambiar
- Routers: solo manejan HTTP
- Services: solo lógica de negocio
- Clients: solo comunicación externa

### Open/Closed Principle (OCP)
- Interfaces permiten agregar nuevas implementaciones sin modificar código existente
- Ejemplo: se puede crear `MockBioTimeService` para testing

### Liskov Substitution Principle (LSP)
- `BioTimeService` puede reemplazar a `IBioTimeService` sin romper funcionalidad
- Permite testing con mocks

### Interface Segregation Principle (ISP)
- Interfaces específicas por funcionalidad
- No hay "god interfaces"

### Dependency Inversion Principle (DIP)
- Módulos de alto nivel (routers) dependen de abstracciones (interfaces)
- No dependen de detalles de implementación

## Extensibilidad

### Agregar un nuevo recurso (ejemplo: Departments)

1. **Crear Schema**:
```python
# app/schemas/biotime/department.py
class DepartmentDto(BaseModel):
    id: int
    name: str
```

2. **Crear Interface**:
```python
# app/services/interfaces/department_service.py
class IDepartmentService(ABC):
    @abstractmethod
    async def get_departments(self) -> List[DepartmentDto]:
        pass
```

3. **Implementar Servicio**:
```python
# app/services/implementations/department_service.py
class DepartmentService(IDepartmentService):
    def __init__(self, client: BioTimeClient):
        self._client = client
    
    async def get_departments(self) -> List[DepartmentDto]:
        # implementación
        pass
```

4. **Crear Router**:
```python
# app/api/v1/routes/departments.py
router = APIRouter(prefix="/departments", tags=["Departments"])

@router.get("")
async def get_departments(service: DepartmentServiceDep):
    return await service.get_departments()
```

5. **Registrar en API**:
```python
# app/api/v1/router.py
from app.api.v1.routes import departments

api_router.include_router(departments.router)
```

## Testing

### Unit Tests
- Mock de dependencias usando interfaces
- Tests aislados de servicios

### Integration Tests
- TestClient de FastAPI
- Validación de contratos de API

## Beneficios de esta Arquitectura

1. **Mantenibilidad**: Fácil de entender y modificar
2. **Testabilidad**: Cada capa se puede testear independientemente
3. **Escalabilidad**: Fácil agregar nuevas funcionalidades
4. **Flexibilidad**: Cambiar implementaciones sin afectar otras capas
5. **Reusabilidad**: Componentes desacoplados y reutilizables
