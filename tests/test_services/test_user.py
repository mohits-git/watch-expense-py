from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
import pytest
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.models.project import Project
from app.models.user import User, UserRole
from app.services.user import UserService


class TestUserService:
    @pytest.fixture
    def mock_password_hasher(self):
        hasher = MagicMock()
        hasher.hash_password.return_value = "hashed_password_123"
        hasher.verify_password.return_value = True
        return hasher

    @pytest.fixture
    def mock_user_repo(self):
        repo = MagicMock()
        repo.save = AsyncMock()
        repo.get = AsyncMock()
        repo.get_by_email = AsyncMock()
        repo.get_all = AsyncMock()
        repo.delete = AsyncMock()
        repo.update = AsyncMock()
        return repo

    @pytest.fixture
    def mock_project_repo(self):
        repo = MagicMock()
        repo.save = AsyncMock()
        repo.get = AsyncMock()
        repo.get_all = AsyncMock()
        repo.update = AsyncMock()
        return repo

    @pytest.fixture
    def user_service(self, mock_password_hasher, mock_user_repo, mock_project_repo):
        return UserService(mock_password_hasher, mock_user_repo, mock_project_repo)

    @pytest.fixture
    def sample_user(self):
        return User.model_validate({
            "id": "",
            "employee_id": "EMP001",
            "name": "Test User",
            "password": "plain_password",
            "email": "test@example.com",
            "role": UserRole.Employee,
            "project_id": "proj-123",
            "department_id": "dept-456",
        })

    @pytest.fixture
    def sample_project(self):
        return Project.model_validate({
            "id": "proj-123",
            "name": "Test Project",
            "description": "Test Description",
            "budget": Decimal("50000.00"),
            "start_date": 1000000,
            "end_date": 2000000,
            "department_id": "dept-456",
        })

    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service, sample_user, mock_password_hasher, mock_user_repo):
        result = await user_service.create_user(sample_user)

        assert result is not None
        assert len(result) > 0
        mock_password_hasher.hash_password.assert_called_once_with("plain_password")
        mock_user_repo.save.assert_called_once()
        saved_user = mock_user_repo.save.call_args[0][0]
        assert saved_user.password == "hashed_password_123"

    @pytest.mark.asyncio
    async def test_create_user_password_required(self, user_service, sample_user):
        sample_user.password = ""

        with pytest.raises(AppException) as exc:
            await user_service.create_user(sample_user)

        assert exc.value.err_code == AppErr.CREATE_USER_PASSWORD_REQUIRED

    @pytest.mark.asyncio
    async def test_update_user_with_password(self, user_service, sample_user, mock_password_hasher, mock_user_repo):
        sample_user.id = uuid4().hex
        sample_user.password = "new_password"

        await user_service.update_user(sample_user)

        mock_password_hasher.hash_password.assert_called_once_with("new_password")
        mock_user_repo.update.assert_called_once()
        updated_user = mock_user_repo.update.call_args[0][0]
        assert updated_user.password == "hashed_password_123"

    @pytest.mark.asyncio
    async def test_update_user_without_password(self, user_service, sample_user, mock_password_hasher, mock_user_repo):
        sample_user.id = uuid4().hex
        sample_user.password = ""

        await user_service.update_user(sample_user)

        mock_password_hasher.hash_password.assert_not_called()
        mock_user_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, user_service, sample_user, mock_user_repo):
        sample_user.id = uuid4().hex
        mock_user_repo.get.return_value = sample_user

        result = await user_service.get_user_by_id(sample_user.id)

        assert result == sample_user
        mock_user_repo.get.assert_called_once_with(sample_user.id)

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, user_service, mock_user_repo):
        mock_user_repo.get.return_value = None

        with pytest.raises(AppException) as exc:
            await user_service.get_user_by_id("non-existent-id")

        assert exc.value.err_code == AppErr.NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_all_users(self, user_service, sample_user, mock_user_repo):
        users_list = [sample_user]
        mock_user_repo.get_all.return_value = users_list

        result = await user_service.get_all_users()

        assert result == users_list
        mock_user_repo.get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_user_success(self, user_service, mock_user_repo):
        curr_user_id = uuid4().hex
        user_to_delete_id = uuid4().hex

        await user_service.delete_user(curr_user_id, user_to_delete_id)

        mock_user_repo.delete.assert_called_once_with(user_to_delete_id)

    @pytest.mark.asyncio
    async def test_delete_user_cannot_delete_self(self, user_service):
        user_id = uuid4().hex

        with pytest.raises(AppException) as exc:
            await user_service.delete_user(user_id, user_id)

        assert exc.value.err_code == AppErr.CANNOT_DELETE_SELF

    @pytest.mark.asyncio
    async def test_get_user_budget_success(self, user_service, sample_user, sample_project, mock_user_repo, mock_project_repo):
        sample_user.id = uuid4().hex
        mock_user_repo.get.return_value = sample_user
        mock_project_repo.get.return_value = sample_project

        result = await user_service.get_user_budget(sample_user.id)

        assert result == 50000.0
        mock_user_repo.get.assert_called_once_with(sample_user.id)
        mock_project_repo.get.assert_called_once_with(sample_user.project_id)

    @pytest.mark.asyncio
    async def test_get_user_budget_user_not_found(self, user_service, mock_user_repo):
        mock_user_repo.get.return_value = None

        with pytest.raises(AppException) as exc:
            await user_service.get_user_budget("non-existent-id")

        assert exc.value.err_code == AppErr.NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_user_budget_no_project(self, user_service, sample_user, mock_user_repo):
        sample_user.id = uuid4().hex
        sample_user.project_id = ""
        mock_user_repo.get.return_value = sample_user

        result = await user_service.get_user_budget(sample_user.id)

        assert result == 0.0

    @pytest.mark.asyncio
    async def test_get_user_budget_project_not_found(self, user_service, sample_user, mock_user_repo, mock_project_repo):
        sample_user.id = uuid4().hex
        mock_user_repo.get.return_value = sample_user
        mock_project_repo.get.return_value = None

        result = await user_service.get_user_budget(sample_user.id)

        assert result == 0.0