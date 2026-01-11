from unittest.mock import MagicMock, AsyncMock
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User, UserRole
from app.dtos.user import UserDTO
from app.dependencies.services import get_user_service
from app.errors.app_exception import AppException
from app.errors.codes import AppErr


@pytest.fixture
def mock_user_service():
    service = MagicMock()
    service.get_user_budget = AsyncMock()
    service.get_all_users = AsyncMock()
    service.create_user = AsyncMock()
    service.get_user_by_id = AsyncMock()
    service.update_user = AsyncMock()
    service.delete_user = AsyncMock()
    return service


@pytest.fixture
def override_user_service(mock_user_service):
    app.dependency_overrides[get_user_service] = lambda: mock_user_service
    yield
    app.dependency_overrides.pop(get_user_service, None)


@pytest.fixture
def sample_user():
    return User.model_validate({
        "id": "user-123",
        "employee_id": "emp-123",
        "name": "Test User",
        "email": "test@example.com",
        "password": "hashed_password",
        "role": UserRole.Employee,
        "budget": 1000.0,
    })


@pytest.fixture
def sample_user_dto(sample_user):
    return UserDTO(**sample_user.model_dump())


@pytest.fixture
def sample_admin_user():
    return User.model_validate({
        "id": "admin-123",
        "employee_id": "emp-123",
        "name": "Admin User",
        "email": "admin@example.com",
        "password": "hashed_password",
        "role": UserRole.Admin,
        "budget": 5000.0,
    })


class TestGetBudget:
    def test_get_budget_success_as_admin(
        self,
        client: TestClient,
        mock_user_service: MagicMock,
        override_auth_admin,
        override_user_service,
        admin_user,
    ):
        mock_user_service.get_user_budget.return_value = 50000.0

        response = client.get("/api/users/budget")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["budget"] == 50000.0
        mock_user_service.get_user_budget.assert_called_once_with(admin_user.user_id)

    def test_get_budget_success_as_employee(
        self,
        client: TestClient,
        mock_user_service: MagicMock,
        override_auth_employee,
        override_user_service,
        employee_user,
    ):
        mock_user_service.get_user_budget.return_value = 25000.0

        response = client.get("/api/users/budget")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["budget"] == 25000.0
        mock_user_service.get_user_budget.assert_called_once_with(employee_user.user_id)

    def test_get_budget_unauthorized_no_token(
        self,
        client: TestClient,
        mock_user_service: MagicMock,
        override_user_service,
        override_auth_unauthenticated,
    ):
        response = client.get("/api/users/budget")
        assert response.status_code == 401


class TestGetUsers:

    def test_get_users_success(
        self,
        client: TestClient,
        mock_user_service: MagicMock,
        override_auth_admin,
        override_user_service,
        sample_user,
        sample_admin_user,
    ):
        users = [sample_user, sample_admin_user]
        mock_user_service.get_all_users.return_value = users

        response = client.get("/api/users/")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        assert data["data"][0]["id"] == sample_user.id
        assert data["data"][1]["id"] == sample_admin_user.id
        mock_user_service.get_all_users.assert_called_once()

    def test_get_users_empty_list(
        self,
        client: TestClient,
        mock_user_service: MagicMock,
        override_auth_admin,
        override_user_service,
    ):
        mock_user_service.get_all_users.return_value = []

        response = client.get("/api/users/")

        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []

    def test_get_users_as_employee_forbidden(
        self,
        client: TestClient,
        mock_user_service: MagicMock,
        override_auth_employee,
        override_user_service,
    ):
        response = client.get("/api/users/")

        assert response.status_code == 403
        mock_user_service.get_all_users.assert_not_called()


class TestCreateUser:

    def test_create_user_success_as_admin(
        self,
        client: TestClient,
        mock_user_service: MagicMock,
        override_auth_admin,
        override_user_service,
    ):
        created_user_id = "new-user-id-123"
        mock_user_service.create_user.return_value = created_user_id

        request_data = {
            "employeeId": "EMP-001",
            "name": "Test User",
            "email": "test@example.com",
            "password": "secure_password",
            "role": "EMPLOYEE",
        }

        response = client.post("/api/users/", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["id"] == created_user_id
        mock_user_service.create_user.assert_called_once()

    def test_create_user_as_employee_forbidden(
        self,
        client: TestClient,
        mock_user_service: MagicMock,
        override_auth_employee,
        override_user_service,
    ):
        request_data = {
            "employeeId": "EMP-001",
            "name": "Test User",
            "email": "test@example.com",
            "password": "secure_password",
            "role": "EMPLOYEE",
        }

        response = client.post("/api/users/", json=request_data)

        assert response.status_code == 403
        mock_user_service.create_user.assert_not_called()

    def test_create_user_validation_error(
        self,
        client: TestClient,
        mock_user_service: MagicMock,
        override_auth_admin,
        override_user_service,
    ):
        request_data = {
            # Missing required employeeId field
            "name": "Test User",
            "email": "invalid-email",  # Invalid: not a valid email format
        }

        response = client.post("/api/users/", json=request_data)

        assert response.status_code == 422
        mock_user_service.create_user.assert_not_called()

    def test_create_user_duplicate_email(
        self,
        client: TestClient,
        mock_user_service: MagicMock,
        override_auth_admin,
        override_user_service,
    ):
        mock_user_service.create_user.side_effect = AppException(
            AppErr.USER_ALREADY_EXISTS
        )

        request_data = {
            "employeeId": "EMP-001",
            "name": "Test User",
            "email": "existing@example.com",
            "password": "secure_password",
            "role": "EMPLOYEE",
        }

        response = client.post("/api/users/", json=request_data)

        assert response.status_code == 409  # Conflict


class TestGetUser:

    def test_get_user_success(
        self,
        client: TestClient,
        mock_user_service: MagicMock,
        override_auth_admin,
        override_user_service,
        sample_user,
    ):
        mock_user_service.get_user_by_id.return_value = sample_user

        response = client.get(f"/api/users/{sample_user.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == sample_user.id
        assert data["data"]["name"] == sample_user.name
        mock_user_service.get_user_by_id.assert_called_once_with(sample_user.id)

    def test_get_user_not_found(
        self,
        client: TestClient,
        mock_user_service: MagicMock,
        override_auth_admin,
        override_user_service,
    ):
        mock_user_service.get_user_by_id.side_effect = AppException(AppErr.NOT_FOUND)

        response = client.get("/api/users/non-existent-id")

        assert response.status_code == 404

    def test_get_user_as_employee_forbidden(
        self,
        client: TestClient,
        mock_user_service: MagicMock,
        override_auth_employee,
        override_user_service,
    ):
        response = client.get("/api/users/some-user-id")

        assert response.status_code == 403
        mock_user_service.get_user_by_id.assert_not_called()


class TestUpdateUser:

    def test_update_user_success_as_admin(
        self,
        client: TestClient,
        mock_user_service: MagicMock,
        override_auth_admin,
        override_user_service,
        sample_user,
    ):
        mock_user_service.update_user.return_value = None

        request_data = {
            "employeeId": "emp-123",
            "name": "Updated Name",
            "email": "updated@example.com",
            "role": "EMPLOYEE",
        }

        response = client.put(f"/api/users/{sample_user.id}", json=request_data)

        assert response.status_code == 200
        response.json()
        mock_user_service.update_user.assert_called_once()

    def test_update_user_as_employee_forbidden(
        self,
        client: TestClient,
        mock_user_service: MagicMock,
        override_auth_employee,
        override_user_service,
        sample_user,
    ):
        request_data = {
            "employeeId": "emp-123",
            "name": "Updated Name",
            "email": "updated@example.com",
            "role": "EMPLOYEE",
        }

        response = client.put(f"/api/users/{sample_user.id}", json=request_data)

        assert response.status_code == 403
        mock_user_service.update_user.assert_not_called()

    def test_update_user_not_found(
        self,
        client: TestClient,
        mock_user_service: MagicMock,
        override_auth_admin,
        override_user_service,
    ):
        mock_user_service.update_user.side_effect = AppException(AppErr.NOT_FOUND)

        request_data = {
            "employeeId": "emp-123",
            "name": "Updated Name",
            "email": "updated@example.com",
            "role": "EMPLOYEE",
        }

        response = client.put("/api/users/non-existent-id", json=request_data)

        assert response.status_code == 404

    def test_update_user_with_password(
        self,
        client: TestClient,
        mock_user_service: MagicMock,
        override_auth_admin,
        override_user_service,
        sample_user,
    ):
        mock_user_service.update_user.return_value = None

        request_data = {
            "employeeId": "emp-123",
            "name": "Updated Name",
            "email": "updated@example.com",
            "role": "ADMIN",
            "password": "new_password",
        }

        response = client.put(f"/api/users/{sample_user.id}", json=request_data)

        assert response.status_code == 200
        response.json()
        mock_user_service.update_user.assert_called_once()


class TestDeleteUser:

    def test_delete_user_success_as_admin(
        self,
        client: TestClient,
        mock_user_service: MagicMock,
        override_auth_admin,
        override_user_service,
        admin_user,
    ):
        mock_user_service.delete_user.return_value = None

        response = client.delete("/api/users/user-to-delete")

        assert response.status_code == 204
        mock_user_service.delete_user.assert_called_once_with(
            admin_user.user_id, "user-to-delete"
        )

    def test_delete_user_as_employee_forbidden(
        self,
        client: TestClient,
        mock_user_service: MagicMock,
        override_auth_employee,
        override_user_service,
    ):
        response = client.delete("/api/users/user-to-delete")

        assert response.status_code == 403
        mock_user_service.delete_user.assert_not_called()

    def test_delete_user_not_found(
        self,
        client: TestClient,
        mock_user_service: MagicMock,
        override_auth_admin,
        override_user_service,
        admin_user,
    ):
        mock_user_service.delete_user.side_effect = AppException(AppErr.NOT_FOUND)

        response = client.delete("/api/users/non-existent-id")

        assert response.status_code == 404
        mock_user_service.delete_user.assert_called_once_with(
            admin_user.user_id, "non-existent-id"
        )

    def test_delete_user_cannot_delete_self(
        self,
        client: TestClient,
        mock_user_service: MagicMock,
        override_auth_admin,
        override_user_service,
        admin_user,
    ):
        mock_user_service.delete_user.side_effect = AppException(
            AppErr.CANNOT_DELETE_SELF
        )

        response = client.delete(f"/api/users/{admin_user.user_id}")

        assert response.status_code == 409
