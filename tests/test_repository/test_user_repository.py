from uuid import uuid4
import pytest
import pytest_asyncio
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.models.user import User, UserRole
from app.repository.user_repository import UserRepository


class TestUserRepository:
    @pytest_asyncio.fixture(scope="class")
    async def user_repository(self, ddb_table, table_name):
        return UserRepository(ddb_table, table_name)

    @pytest_asyncio.fixture(scope="class")
    async def user_id(self) -> str:
        return uuid4().hex

    @pytest_asyncio.fixture(scope="class")
    async def user(self, user_id):
        return User.model_validate({
            "id": user_id,
            "employee_id": "EMP001",
            "name": "Test User",
            "password": "hashed_password_123",
            "email": f"test.user.{uuid4().hex[:8]}@example.com",
            "role": UserRole.Employee,
            "project_id": "proj-123",
            "department_id": "dept-456",
        })

    @pytest.mark.asyncio
    async def test_save(self, user_repository, user):
        await user_repository.save(user)

    @pytest.mark.asyncio
    async def test_save_user_already_exists(self, user_repository, user):
        with pytest.raises(AppException) as app_exc:
            await user_repository.save(user)
        assert app_exc.value.err_code == AppErr.USER_ALREADY_EXISTS

    @pytest.mark.asyncio
    async def test_get(self, user_repository, user):
        result = await user_repository.get(user.id)
        assert result is not None
        assert result.id == user.id
        assert result.employee_id == user.employee_id
        assert result.name == user.name
        assert result.email == user.email
        assert result.role == user.role
        assert result.project_id == user.project_id
        assert result.department_id == user.department_id

    @pytest.mark.asyncio
    async def test_get_non_existent(self, user_repository):
        result = await user_repository.get("non-existent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_email(self, user_repository, user):
        result = await user_repository.get_by_email(user.email)
        assert result is not None
        assert result.id == user.id
        assert result.email == user.email

    @pytest.mark.asyncio
    async def test_get_by_email_non_existent(self, user_repository):
        result = await user_repository.get_by_email("nonexistent@example.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_update(self, user_repository, user):
        user.name = "Updated Name"
        user.employee_id = "EMP002"
        user.role = UserRole.Admin
        user.project_id = "proj-999"

        await user_repository.update(user)

        result = await user_repository.get(user.id)
        assert result is not None
        assert result.name == "Updated Name"
        assert result.employee_id == "EMP002"
        assert result.role == UserRole.Admin
        assert result.project_id == "proj-999"

    @pytest.mark.asyncio
    async def test_update_with_email_change(self, user_repository, user):
        old_email = user.email
        new_email = f"new.email.{uuid4().hex[:8]}@example.com"
        user.email = new_email

        await user_repository.update(user)

        # Verify user can be retrieved by new email
        result = await user_repository.get_by_email(new_email)
        assert result is not None
        assert result.email == new_email
        assert result.id == user.id

        # Verify old email lookup returns None
        old_result = await user_repository.get_by_email(old_email)
        assert old_result is None

    @pytest.mark.asyncio
    async def test_update_non_existent(self, user_repository):
        non_existent_user = User.model_validate({
            "id": "non-existent-id",
            "employee_id": "EMP999",
            "name": "Ghost User",
            "password": "password",
            "email": "ghost@example.com",
            "role": UserRole.Employee,
        })
        with pytest.raises(AppException) as app_exc:
            await user_repository.update(non_existent_user)
        assert app_exc.value.err_code == AppErr.NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete(self, user_repository, user):
        await user_repository.delete(user.id)

        result = await user_repository.get(user.id)
        assert result is None

        email_result = await user_repository.get_by_email(user.email)
        assert email_result is None

    @pytest.mark.asyncio
    async def test_delete_non_existent(self, user_repository):
        with pytest.raises(AppException) as app_exc:
            await user_repository.delete("non-existent-id")
        assert app_exc.value.err_code == AppErr.NOT_FOUND


class TestUserRepositoryGetAll:
    """Test class for get_all with multiple users"""

    @pytest_asyncio.fixture(scope="class")
    async def user_repository(self, ddb_table, table_name):
        return UserRepository(ddb_table, table_name)

    @pytest_asyncio.fixture(scope="class")
    async def setup_users(self, user_repository):
        """Create multiple users for testing get_all"""
        users = [
            User.model_validate({
                "id": uuid4().hex,
                "employee_id": f"EMP{100 + i}",
                "name": f"User {i}",
                "password": f"password{i}",
                "email": f"user{i}.{uuid4().hex[:8]}@example.com",
                "role": UserRole.Admin if i % 2 == 0 else UserRole.Employee,
                "project_id": f"proj-{i}",
                "department_id": f"dept-{i}",
            })
            for i in range(5)
        ]

        for user in users:
            await user_repository.save(user)

        return users

    @pytest.mark.asyncio
    async def test_get_all(self, user_repository, setup_users):
        users = await user_repository.get_all()

        assert len(users) >= 5

        user_ids = {user.id for user in users}
        for user in setup_users:
            assert user.id in user_ids

    @pytest.mark.asyncio
    async def test_get_all_returns_correct_data(self, user_repository, setup_users):
        users = await user_repository.get_all()

        test_user = setup_users[0]
        found_user = next((u for u in users if u.id == test_user.id), None)

        assert found_user is not None
        assert found_user.employee_id == test_user.employee_id
        assert found_user.name == test_user.name
        assert found_user.email == test_user.email
        assert found_user.role == test_user.role
        assert found_user.project_id == test_user.project_id
        assert found_user.department_id == test_user.department_id