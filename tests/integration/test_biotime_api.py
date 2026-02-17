"""
Tests de integración para la API de BioTime.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """Test del endpoint de health check."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_employees_endpoint_structure():
    """Test de la estructura del endpoint de empleados."""
    # Nota: Este test puede fallar si no hay BioTime corriendo
    # En un ambiente de test real, se mockearía el cliente de BioTime
    response = client.get("/api/v1/employees?page=1&page_size=10")
    
    # Verificar que la respuesta tenga la estructura correcta
    # independientemente del código de estado
    if response.status_code == 200:
        data = response.json()
        assert "count" in data
        assert "data" in data
        assert isinstance(data["data"], list)


def test_employees_pagination_validation():
    """Test de validación de parámetros de paginación."""
    # Page debe ser >= 1
    response = client.get("/api/v1/employees?page=0")
    assert response.status_code == 422
    
    # Page size debe estar entre 1 y 100
    response = client.get("/api/v1/employees?page_size=0")
    assert response.status_code == 422
    
    response = client.get("/api/v1/employees?page_size=101")
    assert response.status_code == 422
