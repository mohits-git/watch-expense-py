from unittest.mock import MagicMock, AsyncMock
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User, UserRole, UserClaims
from app.dependencies.services import get_auth_service
from app.dependencies.token_provider import get_token_provider
from app.errors.app_exception import AppException
from app.errors.codes import AppErr


@pytest.fixture
def mock_auth_service():
    service = MagicMock()
    service.login = AsyncMock()
    service.get_current_user = AsyncMock()
    return service


@pytest.fixture
def override_auth_service(mock_auth_service):
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    yield
    app.dependency_overrides.pop(get_auth_service, None)


@pytest.fixture
def mock_token_provider_for_auth():
    provider = MagicMock()
    provider.validate_token.return_value = UserClaims(
        id="user-123",
        name="Test User",
        email="test@example.com",
        role=UserRole.Employee,
    )
    provider.generate_token.return_value = "mock_token"
    return provider


@pytest.fixture
def override_token_provider(mock_token_provider_for_auth):
    app.dependency_overrides[get_token_provider] = lambda: mock_token_provider_for_auth
    yield
    app.dependency_overrides.pop(get_token_provider, None)


@pytest.fixture
def sample_user_for_auth():
    return User.model_validate({
        "id": "user-123",
        "employee_id": "emp-123",
        "name": "Test User",
        "email": "test@example.com",
        "password": "",
        "role": UserRole.Employee,
    })


@pytest.fixture
def sample_admin_user_for_auth():
    return User.model_validate({
        "id": "admin-123",
        "employee_id": "emp-admin",
        "name": "Admin User",
        "email": "admin@example.com",
        "password": "",
        "role": UserRole.Admin,
    })


class TestLogin:
    def test_login_success(
        self,
        client: TestClient,
        mock_auth_service: MagicMock,
        override_auth_service,
    ):
        mock_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        mock_auth_service.login.return_value = mock_token

        request_data = {
            "email": "test@example.com",
            "password": "secure_password",
        }

        response = client.post("/api/auth/login", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["token"] == mock_token
        assert data["message"] == "Logged In Successfully"
        mock_auth_service.login.assert_called_once_with(
            email="test@example.com", password="secure_password"
        )

    def test_login_invalid_credentials(
        self,
        client: TestClient,
        mock_auth_service: MagicMock,
        override_auth_service,
    ):
        mock_auth_service.login.side_effect = AppException(
            AppErr.INVALID_USER_CREDENTIALS
        )

        request_data = {
            "email": "test@example.com",
            "password": "wrong_password",
        }

        response = client.post("/api/auth/login", json=request_data)

        assert response.status_code == 401

    def test_login_user_not_found(
        self,
        client: TestClient,
        mock_auth_service: MagicMock,
        override_auth_service,
    ):
        mock_auth_service.login.side_effect = AppException(
            AppErr.INVALID_USER_CREDENTIALS
        )

        request_data = {
            "email": "nonexistent@example.com",
            "password": "some_password",
        }

        response = client.post("/api/auth/login", json=request_data)

        assert response.status_code == 401

    def test_login_validation_error_missing_email(
        self,
        client: TestClient,
        mock_auth_service: MagicMock,
        override_auth_service,
    ):
        request_data = {
            "password": "secure_password",
        }

        response = client.post("/api/auth/login", json=request_data)

        assert response.status_code == 422
        mock_auth_service.login.assert_not_called()

    def test_login_validation_error_missing_password(
        self,
        client: TestClient,
        mock_auth_service: MagicMock,
        override_auth_service,
    ):
        request_data = {
            "email": "test@example.com",
        }

        response = client.post("/api/auth/login", json=request_data)

        assert response.status_code == 422
        mock_auth_service.login.assert_not_called()

    def test_login_validation_error_invalid_email_format(
        self,
        client: TestClient,
        mock_auth_service: MagicMock,
        override_auth_service,
    ):
        request_data = {
            "email": "not-an-email",
            "password": "secure_password",
        }

        response = client.post("/api/auth/login", json=request_data)

        assert response.status_code == 422
        mock_auth_service.login.assert_not_called()

    def test_login_empty_credentials(
        self,
        client: TestClient,
        mock_auth_service: MagicMock,
        override_auth_service,
    ):
        request_data = {
            "email": "",
            "password": "",
        }

        response = client.post("/api/auth/login", json=request_data)

        assert response.status_code == 422
        mock_auth_service.login.assert_not_called()


class TestAuthMe:
    def test_auth_me_success_as_employee(
        self,
        client: TestClient,
        mock_auth_service: MagicMock,
        mock_token_provider_for_auth: MagicMock,
        override_auth_service,
        override_token_provider,
        sample_user_for_auth,
    ):
        mock_auth_service.get_current_user.return_value = sample_user_for_auth

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer mock_valid_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_user_for_auth.id
        assert data["name"] == sample_user_for_auth.name
        assert data["email"] == sample_user_for_auth.email
        assert data["role"] == "EMPLOYEE"
        assert data.get("password", "") == ""
        mock_auth_service.get_current_user.assert_called_once_with("mock_valid_token")
        mock_token_provider_for_auth.validate_token.assert_called()

    def test_auth_me_success_as_admin(
        self,
        client: TestClient,
        mock_auth_service: MagicMock,
        mock_token_provider_for_auth: MagicMock,
        override_auth_service,
        override_token_provider,
        sample_admin_user_for_auth,
    ):
        mock_token_provider_for_auth.validate_token.return_value = UserClaims(
            id="admin-123",
            name="Admin User",
            email="admin@example.com",
            role=UserRole.Admin,
        )
        mock_auth_service.get_current_user.return_value = sample_admin_user_for_auth

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer mock_valid_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_admin_user_for_auth.id
        assert data["name"] == sample_admin_user_for_auth.name
        assert data["role"] == "ADMIN"

    def test_auth_me_missing_authorization_header(
        self,
        client: TestClient,
        mock_auth_service: MagicMock,
        mock_token_provider_for_auth: MagicMock,
        override_auth_service,
        override_token_provider,
    ):
        response = client.get("/api/auth/me")

        assert response.status_code == 401
        mock_auth_service.get_current_user.assert_not_called()

    def test_auth_me_invalid_token_format(
        self,
        client: TestClient,
        mock_auth_service: MagicMock,
        mock_token_provider_for_auth: MagicMock,
        override_auth_service,
        override_token_provider,
    ):
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "InvalidTokenFormat"}
        )

        assert response.status_code == 401
        mock_auth_service.get_current_user.assert_not_called()

    def test_auth_me_missing_bearer_prefix(
        self,
        client: TestClient,
        mock_auth_service: MagicMock,
        mock_token_provider_for_auth: MagicMock,
        override_auth_service,
        override_token_provider,
    ):
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "mock_token_without_bearer"}
        )

        assert response.status_code == 401
        mock_auth_service.get_current_user.assert_not_called()

    def test_auth_me_expired_token(
        self,
        client: TestClient,
        mock_auth_service: MagicMock,
        mock_token_provider_for_auth: MagicMock,
        override_auth_service,
        override_token_provider,
    ):
        mock_token_provider_for_auth.validate_token.side_effect = AppException(
            AppErr.TOKEN_EXPIRED
        )

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer expired_token"}
        )

        assert response.status_code == 401

    def test_auth_me_invalid_token(
        self,
        client: TestClient,
        mock_auth_service: MagicMock,
        mock_token_provider_for_auth: MagicMock,
        override_auth_service,
        override_token_provider,
    ):
        mock_token_provider_for_auth.validate_token.side_effect = AppException(
            AppErr.UNAUTHORIZED
        )

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    def test_auth_me_user_not_found(
        self,
        client: TestClient,
        mock_auth_service: MagicMock,
        mock_token_provider_for_auth: MagicMock,
        override_auth_service,
        override_token_provider,
    ):
        mock_auth_service.get_current_user.side_effect = AppException(
            AppErr.INVALID, "Invalid user token"
        )

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer valid_token_but_no_user"}
        )

        assert response.status_code == 400
