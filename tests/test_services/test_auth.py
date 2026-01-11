from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
import pytest
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.models.user import User, UserClaims, UserRole
from app.services.auth import AuthService


class TestAuthService:
    @pytest.fixture
    def mock_user_repo(self):
        repo = MagicMock()
        repo.get_by_email = AsyncMock()
        repo.get = AsyncMock()
        return repo

    @pytest.fixture
    def mock_token_provider(self):
        provider = MagicMock()
        provider.generate_token.return_value = "mock_jwt_token"
        provider.validate_token.return_value = UserClaims(
            id=uuid4().hex,
            name="Test User",
            email="test@example.com",
            role=UserRole.Employee
        )
        return provider

    @pytest.fixture
    def mock_password_hasher(self):
        hasher = MagicMock()
        hasher.hash_password.return_value = "hashed_password"
        hasher.verify_password.return_value = True
        return hasher

    @pytest.fixture
    def auth_service(self, mock_user_repo, mock_token_provider, mock_password_hasher):
        return AuthService(mock_user_repo, mock_token_provider, mock_password_hasher)

    @pytest.fixture
    def sample_user(self):
        return User.model_validate({
            "id": uuid4().hex,
            "employee_id": "EMP001",
            "name": "Test User",
            "password": "hashed_password",
            "email": "test@example.com",
            "role": UserRole.Employee,
            "project_id": "proj-123",
            "department_id": "dept-456",
        })

    @pytest.mark.asyncio
    async def test_login_success(self, auth_service, sample_user, mock_user_repo, mock_password_hasher, mock_token_provider):
        mock_user_repo.get_by_email.return_value = sample_user
        mock_password_hasher.verify_password.return_value = True

        token = await auth_service.login("test@example.com", "plain_password")

        assert token == "mock_jwt_token"
        mock_user_repo.get_by_email.assert_called_once_with("test@example.com")
        mock_password_hasher.verify_password.assert_called_once_with(sample_user.password, "plain_password")
        mock_token_provider.generate_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, auth_service, mock_user_repo):
        mock_user_repo.get_by_email.return_value = None

        with pytest.raises(AppException) as exc:
            await auth_service.login("nonexistent@example.com", "password")

        assert exc.value.err_code == AppErr.INVALID_USER_CREDENTIALS

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, auth_service, sample_user, mock_user_repo, mock_password_hasher):
        mock_user_repo.get_by_email.return_value = sample_user
        mock_password_hasher.verify_password.return_value = False

        with pytest.raises(AppException) as exc:
            await auth_service.login("test@example.com", "wrong_password")

        assert exc.value.err_code == AppErr.INVALID_USER_CREDENTIALS

    @pytest.mark.asyncio
    async def test_login_user_no_password(self, auth_service, sample_user, mock_user_repo):
        sample_user.password = ""
        mock_user_repo.get_by_email.return_value = sample_user

        with pytest.raises(AppException) as exc:
            await auth_service.login("test@example.com", "password")

        assert exc.value.err_code == AppErr.INVALID_USER_CREDENTIALS

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, auth_service, sample_user, mock_user_repo, mock_token_provider):
        user_claims = UserClaims(
            id=sample_user.id,
            name=sample_user.name,
            email=sample_user.email,
            role=sample_user.role
        )
        mock_token_provider.validate_token.return_value = user_claims
        mock_user_repo.get.return_value = sample_user

        user = await auth_service.get_current_user("valid_token")

        assert user.id == sample_user.id
        assert user.password == ""
        mock_token_provider.validate_token.assert_called_once_with("valid_token")
        mock_user_repo.get.assert_called_once_with(user_claims.user_id)

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, auth_service, mock_user_repo, mock_token_provider):
        mock_token_provider.validate_token.return_value = UserClaims(
            id="invalid-id",
            name="Test",
            email="test@example.com",
            role=UserRole.Employee
        )
        mock_user_repo.get.return_value = None

        with pytest.raises(Exception) as exc:
            await auth_service.get_current_user("invalid_token")

        assert "Invalid user token" in str(exc.value)

    def test_logout(self, auth_service):
        result = auth_service.logout("some_token")
        assert result is None
