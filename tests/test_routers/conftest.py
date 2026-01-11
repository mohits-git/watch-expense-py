from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import UserClaims, UserRole
from app.dependencies.token_provider import get_token_provider
from app.dependencies.auth import auth_token, authenticated_user


@pytest.fixture
def admin_user():
    return UserClaims(
        id="admin-user-id",
        name="Admin User",
        email="admin@test.com",
        role=UserRole.Admin,
    )


@pytest.fixture
def employee_user():
    return UserClaims(
        id="employee-user-id",
        name="Employee User",
        email="employee@test.com",
        role=UserRole.Employee,
    )


@pytest.fixture
def mock_token_provider(admin_user):
    provider = MagicMock()
    provider.validate_token.return_value = admin_user
    provider.generate_token.return_value = "mock_token"
    return provider


@pytest.fixture
def override_auth_admin(admin_user, mock_token_provider):
    """Override auth dependencies to simulate admin user"""
    mock_token_provider.validate_token.return_value = admin_user

    app.dependency_overrides[get_token_provider] = lambda: mock_token_provider
    app.dependency_overrides[auth_token] = lambda: "mock_token"
    app.dependency_overrides[authenticated_user] = lambda: admin_user
    yield
    app.dependency_overrides.pop(get_token_provider, None)
    app.dependency_overrides.pop(auth_token, None)
    app.dependency_overrides.pop(authenticated_user, None)


@pytest.fixture
def override_auth_employee(employee_user, mock_token_provider):
    """Override auth dependencies to simulate employee user"""
    mock_token_provider.validate_token.return_value = employee_user

    app.dependency_overrides[get_token_provider] = lambda: mock_token_provider
    app.dependency_overrides[auth_token] = lambda: "mock_token"
    app.dependency_overrides[authenticated_user] = lambda: employee_user
    yield
    app.dependency_overrides.pop(get_token_provider, None)
    app.dependency_overrides.pop(auth_token, None)
    app.dependency_overrides.pop(authenticated_user, None)


@pytest.fixture
def override_auth_unauthenticated(mock_token_provider):
    """Override auth dependencies to simulate unauthenticated user"""
    from app.errors.app_exception import AppException
    from app.errors.codes import AppErr

    mock_token_provider.validate_token.side_effect = AppException(AppErr.UNAUTHORIZED)

    app.dependency_overrides[get_token_provider] = lambda: mock_token_provider
    yield
    app.dependency_overrides.pop(get_token_provider, None)


@pytest.fixture
def client():
    return TestClient(app)
