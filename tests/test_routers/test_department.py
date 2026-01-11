from unittest.mock import MagicMock, AsyncMock
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.department import Department
from app.dependencies.services import get_department_service
from app.errors.app_exception import AppException
from app.errors.codes import AppErr


@pytest.fixture
def mock_department_service():
    service = MagicMock()
    service.get_all_departments = AsyncMock()
    service.create_department = AsyncMock()
    service.get_department_by_id = AsyncMock()
    service.update_department = AsyncMock()
    return service


@pytest.fixture
def override_department_service(mock_department_service):
    app.dependency_overrides[get_department_service] = lambda: mock_department_service
    yield
    app.dependency_overrides.pop(get_department_service, None)


@pytest.fixture
def sample_department():
    return Department.model_validate({
        "id": "dept-123",
        "name": "Engineering",
        "budget": Decimal("100000.00"),
        "created_at": 1704067200,
        "updated_at": 1704067200,
    })


@pytest.fixture
def sample_department_2():
    return Department.model_validate({
        "id": "dept-456",
        "name": "Marketing",
        "budget": Decimal("75000.00"),
        "created_at": 1704067200,
        "updated_at": 1704067200,
    })


class TestGetAllDepartments:
    def test_get_all_departments_success_as_admin(
        self,
        client: TestClient,
        mock_department_service: MagicMock,
        override_auth_admin,
        override_department_service,
        sample_department,
        sample_department_2,
    ):
        departments = [sample_department, sample_department_2]
        mock_department_service.get_all_departments.return_value = departments

        response = client.get("/api/admin/departments/")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        assert data["data"][0]["id"] == sample_department.id
        assert data["data"][0]["name"] == sample_department.name
        assert data["data"][1]["id"] == sample_department_2.id
        mock_department_service.get_all_departments.assert_called_once()

    def test_get_all_departments_empty_list(
        self,
        client: TestClient,
        mock_department_service: MagicMock,
        override_auth_admin,
        override_department_service,
    ):
        mock_department_service.get_all_departments.return_value = []

        response = client.get("/api/admin/departments/")

        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []

    def test_get_all_departments_as_employee_forbidden(
        self,
        client: TestClient,
        mock_department_service: MagicMock,
        override_auth_employee,
        override_department_service,
    ):
        response = client.get("/api/admin/departments/")

        assert response.status_code == 403
        mock_department_service.get_all_departments.assert_not_called()

    def test_get_all_departments_unauthorized(
        self,
        client: TestClient,
        mock_department_service: MagicMock,
        override_department_service,
        override_auth_unauthenticated,
    ):
        response = client.get("/api/admin/departments/")

        assert response.status_code == 401


class TestCreateDepartment:
    def test_create_department_success_as_admin(
        self,
        client: TestClient,
        mock_department_service: MagicMock,
        override_auth_admin,
        override_department_service,
    ):
        created_department_id = "new-dept-id-123"
        mock_department_service.create_department.return_value = created_department_id

        request_data = {
            "name": "Human Resources",
            "budget": 80000.00,
        }

        response = client.post("/api/admin/departments/", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["id"] == created_department_id
        mock_department_service.create_department.assert_called_once()

    def test_create_department_as_employee_forbidden(
        self,
        client: TestClient,
        mock_department_service: MagicMock,
        override_auth_employee,
        override_department_service,
    ):
        request_data = {
            "name": "Human Resources",
            "budget": 80000.00,
        }

        response = client.post("/api/admin/departments/", json=request_data)

        assert response.status_code == 403
        mock_department_service.create_department.assert_not_called()

    def test_create_department_validation_error(
        self,
        client: TestClient,
        mock_department_service: MagicMock,
        override_auth_admin,
        override_department_service,
    ):
        request_data = {
            # Missing required fields
            "name": "HR",
        }

        response = client.post("/api/admin/departments/", json=request_data)

        assert response.status_code == 422
        mock_department_service.create_department.assert_not_called()

    def test_create_department_invalid_budget(
        self,
        client: TestClient,
        mock_department_service: MagicMock,
        override_auth_admin,
        override_department_service,
    ):
        request_data = {
            "name": "Human Resources",
            "budget": "invalid_budget",
        }

        response = client.post("/api/admin/departments/", json=request_data)

        assert response.status_code == 422
        mock_department_service.create_department.assert_not_called()

    def test_create_department_negative_budget(
        self,
        client: TestClient,
        mock_department_service: MagicMock,
        override_auth_admin,
        override_department_service,
    ):
        request_data = {
            "name": "Human Resources",
            "budget": -1000.00,
        }

        response = client.post("/api/admin/departments/", json=request_data)

        assert response.status_code == 422


class TestGetDepartmentById:
    def test_get_department_by_id_success(
        self,
        client: TestClient,
        mock_department_service: MagicMock,
        override_auth_admin,
        override_department_service,
        sample_department,
    ):
        mock_department_service.get_department_by_id.return_value = sample_department

        response = client.get(f"/api/admin/departments/{sample_department.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == sample_department.id
        assert data["data"]["name"] == sample_department.name
        assert data["data"]["budget"] == float(sample_department.budget)
        mock_department_service.get_department_by_id.assert_called_once_with(sample_department.id)

    def test_get_department_by_id_not_found(
        self,
        client: TestClient,
        mock_department_service: MagicMock,
        override_auth_admin,
        override_department_service,
    ):
        mock_department_service.get_department_by_id.side_effect = AppException(AppErr.NOT_FOUND)

        response = client.get("/api/admin/departments/non-existent-id")

        assert response.status_code == 404

    def test_get_department_by_id_as_employee_forbidden(
        self,
        client: TestClient,
        mock_department_service: MagicMock,
        override_auth_employee,
        override_department_service,
    ):
        response = client.get("/api/admin/departments/some-dept-id")

        assert response.status_code == 403
        mock_department_service.get_department_by_id.assert_not_called()


class TestUpdateDepartment:
    def test_update_department_success_as_admin(
        self,
        client: TestClient,
        mock_department_service: MagicMock,
        override_auth_admin,
        override_department_service,
        sample_department,
    ):
        mock_department_service.update_department.return_value = None

        request_data = {
            "name": "Engineering - Updated",
            "budget": 120000.00,
        }

        response = client.put(f"/api/admin/departments/{sample_department.id}", json=request_data)

        assert response.status_code == 200
        mock_department_service.update_department.assert_called_once()

    def test_update_department_as_employee_forbidden(
        self,
        client: TestClient,
        mock_department_service: MagicMock,
        override_auth_employee,
        override_department_service,
        sample_department,
    ):
        request_data = {
            "name": "Engineering - Updated",
            "budget": 120000.00,
        }

        response = client.put(f"/api/admin/departments/{sample_department.id}", json=request_data)

        assert response.status_code == 403
        mock_department_service.update_department.assert_not_called()

    def test_update_department_not_found(
        self,
        client: TestClient,
        mock_department_service: MagicMock,
        override_auth_admin,
        override_department_service,
    ):
        mock_department_service.update_department.side_effect = AppException(AppErr.NOT_FOUND)

        request_data = {
            "name": "Engineering - Updated",
            "budget": 120000.00,
        }

        response = client.put("/api/admin/departments/non-existent-id", json=request_data)

        assert response.status_code == 404

    def test_update_department_validation_error(
        self,
        client: TestClient,
        mock_department_service: MagicMock,
        override_auth_admin,
        override_department_service,
        sample_department,
    ):
        request_data = {
            "name": "Updated Name",
            # Missing required budget field
        }

        response = client.put(f"/api/admin/departments/{sample_department.id}", json=request_data)

        assert response.status_code == 422
        mock_department_service.update_department.assert_not_called()

    def test_update_department_name_only(
        self,
        client: TestClient,
        mock_department_service: MagicMock,
        override_auth_admin,
        override_department_service,
        sample_department,
    ):
        mock_department_service.update_department.return_value = None

        request_data = {
            "name": "Engineering Division",
            "budget": 100000.00,  # Keep same budget
        }

        response = client.put(f"/api/admin/departments/{sample_department.id}", json=request_data)

        assert response.status_code == 200
        mock_department_service.update_department.assert_called_once()

    def test_update_department_budget_only(
        self,
        client: TestClient,
        mock_department_service: MagicMock,
        override_auth_admin,
        override_department_service,
        sample_department,
    ):
        mock_department_service.update_department.return_value = None

        request_data = {
            "name": "Engineering",  # Keep same name
            "budget": 150000.00,
        }

        response = client.put(f"/api/admin/departments/{sample_department.id}", json=request_data)

        assert response.status_code == 200
        mock_department_service.update_department.assert_called_once()
