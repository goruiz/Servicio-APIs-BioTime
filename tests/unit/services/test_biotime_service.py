"""
Tests unitarios para BioTimeService.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.schemas.biotime.employee import EmployeeDto
from app.schemas.biotime.common import PaginatedResponse
from app.services.biotime_service import BioTimeService


@pytest.mark.asyncio
async def test_get_employees_success():
    """Test obtener empleados exitosamente."""
    # Arrange
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value={
        "count": 2,
        "next": None,
        "previous": None,
        "data": [
            {
                "id": 1,
                "emp_code": "EMP001",
                "first_name": "Juan",
                "last_name": "Pérez",
                "department": 1,
                "position": 2,
                "hire_date": "2024-01-15"
            },
            {
                "id": 2,
                "emp_code": "EMP002",
                "first_name": "María",
                "last_name": "García",
                "department": 1,
                "position": 3,
                "hire_date": "2024-02-01"
            }
        ]
    })
    
    service = BioTimeService(client=mock_client)
    
    # Act
    result = await service.get_employees(page=1, page_size=10)
    
    # Assert
    assert isinstance(result, PaginatedResponse)
    assert result.count == 2
    assert len(result.data) == 2
    assert isinstance(result.data[0], EmployeeDto)
    assert result.data[0].emp_code == "EMP001"
    
    # Verificar que se llamó al cliente correctamente
    mock_client.get.assert_called_once_with(
        "personnel/api/employees/",
        params={"page": 1, "page_size": 10}
    )


@pytest.mark.asyncio
async def test_get_employees_empty():
    """Test obtener empleados cuando no hay datos."""
    # Arrange
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value={
        "count": 0,
        "next": None,
        "previous": None,
        "data": []
    })
    
    service = BioTimeService(client=mock_client)
    
    # Act
    result = await service.get_employees(page=1, page_size=10)
    
    # Assert
    assert result.count == 0
    assert len(result.data) == 0
