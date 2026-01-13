from unittest.mock import patch, MagicMock
import pytest
from botocore.exceptions import ClientError
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.models.user import User, UserRole
from app.repository.user_repository import UserRepository


@pytest.fixture
def user_repository(mock_ddb_table, table_name):
    return UserRepository(mock_ddb_table, table_name)


@pytest.fixture
def sample_user():
    return User.model_validate({
        "id": "user-123",
        "employee_id": "EMP001",
        "name": "Test User",
        "password": "hashed_password_123",
        "email": "testuser@example.com",
        "role": UserRole.Employee,
        "project_id": "proj-123",
        "department_id": "dept-456",
        "created_at": 1704067200000,
        "updated_at": 1704067200000,
    })


@pytest.fixture
def sample_user_item():
    return {
        "PK": "USER#user-123",
        "SK": "PROFILE",
        "UserID": "user-123",
        "EmployeeID": "EMP001",
        "Name": "Test User",
        "PasswordHash": "hashed_password_123",
        "Email": "testuser@example.com",
        "Role": "EMPLOYEE",
        "ProjectID": "proj-123",
        "DepartmentID": "dept-456",
        "CreatedAt": 1704067200000,
        "UpdatedAt": 1704067200000,
    }


class TestUserRepositorySave:
    @pytest.mark.asyncio
    @patch("uuid.uuid4")
    @patch("time.time_ns")
    async def test_save_success(
        self,
        mock_time_ns,
        mock_uuid,
        user_repository,
        mock_ddb_table,
    ):
        mock_uuid.return_value.hex = "new-user-id"
        mock_time_ns.return_value = 1704067200000000000
        mock_ddb_table.meta.client.transact_write_items.return_value = None

        user = User.model_validate({
            "employee_id": "EMP002",
            "name": "New User",
            "password": "hashed_password",
            "email": "newuser@example.com",
            "role": UserRole.Employee,
            "project_id": "proj-456",
            "department_id": "dept-789",
        })

        await user_repository.save(user)

        mock_ddb_table.meta.client.transact_write_items.assert_called_once()
        call_args = mock_ddb_table.meta.client.transact_write_items.call_args[1]
        assert len(call_args["TransactItems"]) == 3
        assert all("Put" in item for item in call_args["TransactItems"])

    @pytest.mark.asyncio
    @patch("app.repository.utils.is_conditional_check_failure")
    async def test_save_user_already_exists(
        self,
        mock_is_conditional_check_failure,
        user_repository,
        mock_ddb_table,
        sample_user,
    ):
        error_response = {"Error": {"Code": "TransactionCanceledException"}}
        mock_ddb_table.meta.client.transact_write_items.side_effect = ClientError(
            error_response, "TransactWriteItems"
        )
        mock_is_conditional_check_failure.return_value = True

        with pytest.raises(AppException) as exc_info:
            await user_repository.save(sample_user)

        assert exc_info.value.err_code == AppErr.USER_ALREADY_EXISTS


class TestUserRepositoryGet:
    @pytest.mark.asyncio
    async def test_get_success(
        self,
        user_repository,
        mock_ddb_table,
        sample_user_item,
    ):
        mock_ddb_table.get_item.return_value = {"Item": sample_user_item}

        result = await user_repository.get("user-123")

        assert result is not None
        assert result.id == "user-123"
        assert result.employee_id == "EMP001"
        assert result.name == "Test User"
        assert result.email == "testuser@example.com"
        assert result.role == UserRole.Employee
        mock_ddb_table.get_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_not_found(
        self,
        user_repository,
        mock_ddb_table,
    ):
        mock_ddb_table.get_item.return_value = {}

        result = await user_repository.get("non-existent-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_email_success(
        self,
        user_repository,
        mock_ddb_table,
        sample_user_item,
    ):
        mock_ddb_table.get_item.return_value = {"Item": sample_user_item}

        result = await user_repository.get_by_email("testuser@example.com")

        assert result is not None
        assert result.id == "user-123"
        assert result.email == "testuser@example.com"
        mock_ddb_table.get_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_email_not_found(
        self,
        user_repository,
        mock_ddb_table,
    ):
        mock_ddb_table.get_item.return_value = {}

        result = await user_repository.get_by_email("nonexistent@example.com")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_client_error(
        self,
        user_repository,
        mock_ddb_table,
    ):
        error_response = {"Error": {"Code": "ResourceNotFoundException"}}
        mock_ddb_table.get_item.side_effect = ClientError(error_response, "GetItem")

        with pytest.raises(AppException) as exc_info:
            await user_repository.get("user-123")

        assert exc_info.value.err_code == AppErr.INTERNAL


class TestUserRepositoryGetAll:
    @pytest.mark.asyncio
    @patch("app.repository.utils.query_items")
    async def test_get_all_success(
        self,
        mock_query_items,
        user_repository,
    ):
        mock_query_items.return_value = [
            {
                "UserID": "user-1",
                "EmployeeID": "EMP100",
                "Name": "User 1",
                "PasswordHash": "password1",
                "Email": "user1@example.com",
                "Role": "EMPLOYEE",
                "ProjectID": "proj-1",
                "DepartmentID": "dept-1",
                "CreatedAt": 1704067200000,
                "UpdatedAt": 1704067200000,
            },
            {
                "UserID": "user-2",
                "EmployeeID": "EMP101",
                "Name": "User 2",
                "PasswordHash": "password2",
                "Email": "user2@example.com",
                "Role": "ADMIN",
                "ProjectID": "proj-2",
                "DepartmentID": "dept-2",
                "CreatedAt": 1704067300000,
                "UpdatedAt": 1704067300000,
            },
        ]

        users = await user_repository.get_all()

        assert len(users) == 2
        assert users[0].id == "user-1"
        assert users[0].name == "User 1"
        assert users[0].role == UserRole.Employee
        assert users[1].id == "user-2"
        assert users[1].name == "User 2"
        assert users[1].role == UserRole.Admin

    @pytest.mark.asyncio
    @patch("app.repository.utils.query_items")
    async def test_get_all_empty(
        self,
        mock_query_items,
        user_repository,
    ):
        mock_query_items.return_value = []

        users = await user_repository.get_all()

        assert len(users) == 0


class TestUserRepositoryUpdate:
    @pytest.mark.asyncio
    @patch("time.time_ns")
    async def test_update_success(
        self,
        mock_time_ns,
        user_repository,
        mock_ddb_table,
        sample_user,
        sample_user_item,
    ):
        mock_time_ns.return_value = 1704070800000000000
        mock_ddb_table.get_item.return_value = {"Item": sample_user_item}
        mock_ddb_table.meta.client.transact_write_items.return_value = None

        sample_user.name = "Updated Name"
        sample_user.employee_id = "EMP002"
        sample_user.role = UserRole.Admin

        await user_repository.update(sample_user)

        mock_ddb_table.get_item.assert_called_once()
        mock_ddb_table.meta.client.transact_write_items.assert_called_once()
        call_args = mock_ddb_table.meta.client.transact_write_items.call_args[1]
        assert len(call_args["TransactItems"]) == 3
        assert all("Update" in item for item in call_args["TransactItems"])

    @pytest.mark.asyncio
    @patch("time.time_ns")
    async def test_update_with_email_change(
        self,
        mock_time_ns,
        user_repository,
        mock_ddb_table,
        sample_user,
        sample_user_item,
    ):
        mock_time_ns.return_value = 1704070800000000000
        mock_ddb_table.get_item.return_value = {"Item": sample_user_item}
        mock_ddb_table.meta.client.transact_write_items.return_value = None

        sample_user.email = "newemail@example.com"

        await user_repository.update(sample_user)

        mock_ddb_table.get_item.assert_called_once()
        mock_ddb_table.meta.client.transact_write_items.assert_called_once()
        call_args = mock_ddb_table.meta.client.transact_write_items.call_args[1]
        assert len(call_args["TransactItems"]) == 4
        assert sum(1 for item in call_args["TransactItems"] if "Update" in item) == 2
        assert sum(1 for item in call_args["TransactItems"] if "Delete" in item) == 1
        assert sum(1 for item in call_args["TransactItems"] if "Put" in item) == 1

    @pytest.mark.asyncio
    async def test_update_not_found(
        self,
        user_repository,
        mock_ddb_table,
        sample_user,
    ):
        mock_ddb_table.get_item.return_value = {}

        with pytest.raises(AppException) as exc_info:
            await user_repository.update(sample_user)

        assert exc_info.value.err_code == AppErr.NOT_FOUND


class TestUserRepositoryDelete:
    @pytest.mark.asyncio
    async def test_delete_success(
        self,
        user_repository,
        mock_ddb_table,
        sample_user_item,
    ):
        mock_ddb_table.get_item.return_value = {"Item": sample_user_item}
        mock_batch_writer = MagicMock()
        mock_ddb_table.batch_writer.return_value.__enter__.return_value = mock_batch_writer

        await user_repository.delete("user-123")

        mock_ddb_table.get_item.assert_called_once()
        mock_ddb_table.batch_writer.assert_called_once()
        assert mock_batch_writer.delete_item.call_count == 3

    @pytest.mark.asyncio
    async def test_delete_not_found(
        self,
        user_repository,
        mock_ddb_table,
    ):
        mock_ddb_table.get_item.return_value = {}

        with pytest.raises(AppException) as exc_info:
            await user_repository.delete("non-existent-id")

        assert exc_info.value.err_code == AppErr.NOT_FOUND
