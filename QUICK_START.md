# Guía de Inicio Rápido

## 🚀 Puesta en Marcha en 5 Minutos

### 1. Verificar Python

```bash
python --version  # Debe ser Python 3.12+
```

### 2. Crear y Activar Entorno Virtual

**Linux/Mac:**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env con tus credenciales de BioTime
nano .env  # o usa tu editor favorito
```

**Configuración mínima requerida:**
```env
BIOTIME_BASE_URL=http://tu-servidor-biotime:8081/
BIOTIME_USERNAME=tu_usuario
BIOTIME_PASSWORD=tu_password
```

### 5. Ejecutar la Aplicación

**Opción A - Script automático:**
```bash
# Linux/Mac
./run.sh

# Windows
run.bat
```

**Opción B - Manual:**
```bash
python -m app.main
```

**Opción C - Con uvicorn:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Verificar que Funciona

Abre tu navegador en:

- **API Docs (Swagger)**: http://localhost:8000/api/v1/docs
- **Health Check**: http://localhost:8000/health

## 📝 Probar el Endpoint de Empleados

### Usando curl:

```bash
curl http://localhost:8000/api/v1/employees?page=1&page_size=10
```

### Usando Swagger UI:

1. Ve a http://localhost:8000/api/v1/docs
2. Expande el endpoint `GET /api/v1/employees`
3. Haz click en "Try it out"
4. Ajusta los parámetros page y page_size
5. Haz click en "Execute"

### Respuesta esperada:

```json
{
  "count": 100,
  "next": "http://localhost:8000/api/v1/employees/?page=2",
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

## 🧪 Ejecutar Tests

```bash
# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# Ejecutar todos los tests
pytest

# Con reporte de cobertura
pytest --cov=app --cov-report=html

# Ver reporte en navegador
open htmlcov/index.html  # Mac/Linux
start htmlcov/index.html  # Windows
```

## 🐛 Solución de Problemas

### Error: "No module named 'app'"

**Solución:** Asegúrate de estar en el directorio raíz del proyecto y ejecutar:
```bash
python -m app.main
```

### Error: "pydantic_core._pydantic_core.ValidationError"

**Solución:** Verifica que tu archivo `.env` tenga todas las variables requeridas:
```env
BIOTIME_BASE_URL=...
BIOTIME_USERNAME=...
BIOTIME_PASSWORD=...
```

### Error: "Connection refused" o "502 Bad Gateway"

**Solución:** Verifica que:
1. BioTime esté corriendo
2. La URL en BIOTIME_BASE_URL sea correcta
3. Puedas hacer ping al servidor de BioTime

### Error de autenticación (401)

**Solución:** 
1. Verifica usuario y contraseña en `.env`
2. Prueba hacer login directo a BioTime
3. Revisa los logs del servicio

## 📚 Próximos Pasos

1. **Leer la arquitectura**: Revisa `ARCHITECTURE.md`
2. **Ver la estructura**: Abre `STRUCTURE.txt`
3. **Agregar nuevos endpoints**: Sigue el patrón en `app/api/v1/routes/employees.py`
4. **Escribir tests**: Usa los ejemplos en `tests/`

## 🔗 Enlaces Útiles

- Documentación completa: `README.md`
- Arquitectura detallada: `ARCHITECTURE.md`
- Estructura del proyecto: `STRUCTURE.txt`

## 💡 Tips

- Usa `DEBUG=True` en desarrollo para logs más detallados
- El servicio recarga automáticamente con `--reload` al guardar cambios
- Swagger UI es interactivo: puedes probar los endpoints directamente
- Los logs JSON en producción son más fáciles de parsear

## 🆘 Ayuda

Si encuentras problemas:
1. Revisa los logs del servicio
2. Verifica la configuración en `.env`
3. Asegúrate de que BioTime esté accesible
4. Consulta la documentación de FastAPI
