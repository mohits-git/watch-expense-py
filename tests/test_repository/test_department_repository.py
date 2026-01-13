from decimal import Decimal
from unittest.mock import patch
import pytest
from botocore.exceptions import ClientError
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.models.department import Department
from app.repository.department_repository import DepartmentRepository


@pytest.fixture
def department_repository(mock_ddb_table, table_name):
    return DepartmentRepository(mock_ddb_table, table_name)


@pytest.fixture
def sample_department():
    return Department.model_validate({
        "id": "dept-123",
        "name": "Test Department",
        "budget": Decimal("50000.00"),
        "created_at": 1704067200000,
        "updated_at": 1704067200000,
    })


@pytest.fixture
def sample_department_item():
    return {
        "PK": "DEPARTMENT#dept-123",
        "SK": "DETAILS",
        "DepartmentID": "dept-123",
        "Name": "Test Department",
        "Budget": Decimal("50000.00"),
        "CreatedAt": 1704067200000,
        "UpdatedAt": 1704067200000,
    }


class TestDepartmentRepositorySave:
    @pytest.mark.asyncio
    @patch("uuid.uuid4")
    @patch("time.time_ns")
    async def test_save_success(
        self,
        mock_time_ns,
        mock_uuid,
        department_repository,
        mock_ddb_table,
    ):
        mock_uuid.return_value.hex = "new-dept-id"
        mock_time_ns.return_value = 1704067200000000000
        mock_ddb_table.meta.client.transact_write_items.return_value = None

        department = Department.model_validate({
            "name": "New Department",
            "budget": Decimal("75000.00"),
        })

        await department_repository.save(department)

        mock_ddb_table.meta.client.transact_write_items.assert_called_once()
        call_args = mock_ddb_table.meta.client.transact_write_items.call_args[1]
        assert len(call_args["TransactItems"]) == 2
        assert all("Put" in item for item in call_args["TransactItems"])

    @pytest.mark.asyncio
    @patch("app.repository.utils.is_conditional_check_failure")
    async def test_save_department_already_exists(
        self,
        mock_is_conditional_check_failure,
        department_repository,
        mock_ddb_table,
        sample_department,
    ):
        error_response = {"Error": {"Code": "TransactionCanceledException"}}
        mock_ddb_table.meta.client.transact_write_items.side_effect = ClientError(
            error_response, "TransactWriteItems"
        )
        mock_is_conditional_check_failure.return_value = True

        with pytest.raises(AppException) as exc_info:
            await department_repository.save(sample_department)

        assert exc_info.value.err_code == AppErr.DEPARTMENT_ALREADY_EXISTS


class TestDepartmentRepositoryGet:
    @pytest.mark.asyncio
    async def test_get_success(
        self,
        department_repository,
        mock_ddb_table,
        sample_department_item,
    ):
        mock_ddb_table.get_item.return_value = {"Item": sample_department_item}

        result = await department_repository.get("dept-123")

        assert result is not None
        assert result.id == "dept-123"
        assert result.name == "Test Department"
        assert result.budget == Decimal("50000.00")
        mock_ddb_table.get_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_not_found(
        self,
        department_repository,
        mock_ddb_table,
    ):
        mock_ddb_table.get_item.return_value = {}

        result = await department_repository.get("non-existent-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_client_error(
        self,
        department_repository,
        mock_ddb_table,
    ):
        error_response = {"Error": {"Code": "ResourceNotFoundException"}}
        mock_ddb_table.get_item.side_effect = ClientError(error_response, "GetItem")

        with pytest.raises(AppException) as exc_info:
            await department_repository.get("dept-123")

        assert exc_info.value.err_code == AppErr.INTERNAL


class TestDepartmentRepositoryGetAll:
    @pytest.mark.asyncio
    @patch("app.repository.utils.query_items")
    async def test_get_all_success(
        self,
        mock_query_items,
        department_repository,
    ):
        mock_query_items.return_value = [
            {
                "DepartmentID": "dept-1",
                "Name": "Department 1",
                "Budget": Decimal("10000.00"),
                "CreatedAt": 1704067200000,
                "UpdatedAt": 1704067200000,
            },
            {
                "DepartmentID": "dept-2",
                "Name": "Department 2",
                "Budget": Decimal("20000.00"),
                "CreatedAt": 1704067300000,
                "UpdatedAt": 1704067300000,
            },
        ]

        departments = await department_repository.get_all()

        assert len(departments) == 2
        assert departments[0].id == "dept-1"
        assert departments[0].name == "Department 1"
        assert departments[1].id == "dept-2"
        assert departments[1].name == "Department 2"

    @pytest.mark.asyncio
    @patch("app.repository.utils.query_items")
    async def test_get_all_empty(
        self,
        mock_query_items,
        department_repository,
    ):
        mock_query_items.return_value = []

        departments = await department_repository.get_all()

        assert len(departments) == 0


class TestDepartmentRepositoryUpdate:
    @pytest.mark.asyncio
    @patch("time.time_ns")
    async def test_update_success(
        self,
        mock_time_ns,
        department_repository,
        mock_ddb_table,
        sample_department,
        sample_department_item,
    ):
        mock_time_ns.return_value = 1704070800000000000
        mock_ddb_table.get_item.return_value = {"Item": sample_department_item}
        mock_ddb_table.meta.client.transact_write_items.return_value = None

        sample_department.name = "Updated Department Name"
        sample_department.budget = Decimal("75000.00")

        await department_repository.update(sample_department)

        mock_ddb_table.get_item.assert_called_once()
        mock_ddb_table.meta.client.transact_write_items.assert_called_once()
        call_args = mock_ddb_table.meta.client.transact_write_items.call_args[1]
        assert len(call_args["TransactItems"]) == 2
        assert all("Update" in item for item in call_args["TransactItems"])

    @pytest.mark.asyncio
    async def test_update_not_found(
        self,
        department_repository,
        mock_ddb_table,
        sample_department,
    ):
        mock_ddb_table.get_item.return_value = {}

        with pytest.raises(AppException) as exc_info:
            await department_repository.update(sample_department)

        assert exc_info.value.err_code == AppErr.NOT_FOUND
