from decimal import Decimal
from unittest.mock import patch
import pytest
from botocore.exceptions import ClientError
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.models.project import Project
from app.repository.project_repository import ProjectRepository


@pytest.fixture
def project_repository(mock_ddb_table, table_name):
    return ProjectRepository(mock_ddb_table, table_name)


@pytest.fixture
def sample_project():
    return Project.model_validate({
        "id": "project-123",
        "name": "Test Project",
        "description": "Test Description",
        "budget": Decimal("10000.00"),
        "start_date": 1704067200000,
        "end_date": 1704153600000,
        "department_id": "dept-456",
        "created_at": 1704067200000,
        "updated_at": 1704067200000,
    })


@pytest.fixture
def sample_project_item():
    return {
        "PK": "PROJECT#project-123",
        "SK": "DETAILS",
        "ProjectID": "project-123",
        "Name": "Test Project",
        "Description": "Test Description",
        "Budget": Decimal("10000.00"),
        "StartDate": 1704067200000,
        "EndDate": 1704153600000,
        "DepartmentID": "dept-456",
        "CreatedAt": 1704067200000,
        "UpdatedAt": 1704067200000,
    }


class TestProjectRepositorySave:
    @pytest.mark.asyncio
    @patch("uuid.uuid4")
    @patch("time.time_ns")
    async def test_save_success(
        self,
        mock_time_ns,
        mock_uuid,
        project_repository,
        mock_ddb_table,
    ):
        mock_uuid.return_value.hex = "new-project-id"
        mock_time_ns.return_value = 1704067200000000000
        mock_ddb_table.meta.client.transact_write_items.return_value = None

        project = Project.model_validate({
            "name": "New Project",
            "description": "New Description",
            "budget": Decimal("15000.00"),
            "start_date": 1704067200000,
            "end_date": 1704153600000,
            "department_id": "dept-789",
        })

        await project_repository.save(project)

        mock_ddb_table.meta.client.transact_write_items.assert_called_once()
        call_args = mock_ddb_table.meta.client.transact_write_items.call_args[1]
        assert len(call_args["TransactItems"]) == 3
        assert all("Put" in item for item in call_args["TransactItems"])

    @pytest.mark.asyncio
    @patch("app.repository.utils.is_conditional_check_failure")
    async def test_save_project_already_exists(
        self,
        mock_is_conditional_check_failure,
        project_repository,
        mock_ddb_table,
        sample_project,
    ):
        error_response = {"Error": {"Code": "TransactionCanceledException"}}
        mock_ddb_table.meta.client.transact_write_items.side_effect = ClientError(
            error_response, "TransactWriteItems"
        )
        mock_is_conditional_check_failure.return_value = True

        with pytest.raises(AppException) as exc_info:
            await project_repository.save(sample_project)

        assert exc_info.value.err_code == AppErr.PROJECT_ALREADY_EXISTS


class TestProjectRepositoryGet:
    @pytest.mark.asyncio
    async def test_get_success(
        self,
        project_repository,
        mock_ddb_table,
        sample_project_item,
    ):
        mock_ddb_table.get_item.return_value = {"Item": sample_project_item}

        result = await project_repository.get("project-123")

        assert result is not None
        assert result.id == "project-123"
        assert result.name == "Test Project"
        assert result.description == "Test Description"
        assert result.budget == Decimal("10000.00")
        assert result.department_id == "dept-456"
        mock_ddb_table.get_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_not_found(
        self,
        project_repository,
        mock_ddb_table,
    ):
        mock_ddb_table.get_item.return_value = {}

        result = await project_repository.get("non-existent-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_client_error(
        self,
        project_repository,
        mock_ddb_table,
    ):
        error_response = {"Error": {"Code": "ResourceNotFoundException"}}
        mock_ddb_table.get_item.side_effect = ClientError(error_response, "GetItem")

        with pytest.raises(AppException) as exc_info:
            await project_repository.get("project-123")

        assert exc_info.value.err_code == AppErr.INTERNAL


class TestProjectRepositoryGetAll:
    @pytest.mark.asyncio
    @patch("app.repository.utils.query_items")
    async def test_get_all_success(
        self,
        mock_query_items,
        project_repository,
    ):
        mock_query_items.return_value = [
            {
                "ProjectID": "project-1",
                "Name": "Project 1",
                "Description": "Desc 1",
                "Budget": Decimal("10000.00"),
                "StartDate": 1704067200000,
                "EndDate": 1704153600000,
                "DepartmentID": "dept-1",
                "CreatedAt": 1704067200000,
                "UpdatedAt": 1704067200000,
            },
            {
                "ProjectID": "project-2",
                "Name": "Project 2",
                "Description": "Desc 2",
                "Budget": Decimal("20000.00"),
                "StartDate": 1704067200000,
                "EndDate": 1704153600000,
                "DepartmentID": "dept-2",
                "CreatedAt": 1704067300000,
                "UpdatedAt": 1704067300000,
            },
        ]

        projects = await project_repository.get_all()

        assert len(projects) == 2
        assert projects[0].id == "project-1"
        assert projects[0].name == "Project 1"
        assert projects[1].id == "project-2"
        assert projects[1].name == "Project 2"

    @pytest.mark.asyncio
    @patch("app.repository.utils.query_items")
    async def test_get_all_empty(
        self,
        mock_query_items,
        project_repository,
    ):
        mock_query_items.return_value = []

        projects = await project_repository.get_all()

        assert len(projects) == 0


class TestProjectRepositoryUpdate:
    @pytest.mark.asyncio
    @patch("time.time_ns")
    async def test_update_success(
        self,
        mock_time_ns,
        project_repository,
        mock_ddb_table,
        sample_project,
        sample_project_item,
    ):
        mock_time_ns.return_value = 1704070800000000000
        mock_ddb_table.get_item.return_value = {"Item": sample_project_item}
        mock_ddb_table.meta.client.transact_write_items.return_value = None

        sample_project.name = "Updated Project Name"
        sample_project.budget = Decimal("20000.00")

        await project_repository.update(sample_project)

        mock_ddb_table.get_item.assert_called_once()
        mock_ddb_table.meta.client.transact_write_items.assert_called_once()
        call_args = mock_ddb_table.meta.client.transact_write_items.call_args[1]
        assert len(call_args["TransactItems"]) == 3
        assert all("Update" in item for item in call_args["TransactItems"])

    @pytest.mark.asyncio
    @patch("time.time_ns")
    async def test_update_with_department_change(
        self,
        mock_time_ns,
        project_repository,
        mock_ddb_table,
        sample_project,
        sample_project_item,
    ):
        mock_time_ns.return_value = 1704070800000000000
        mock_ddb_table.get_item.return_value = {"Item": sample_project_item}
        mock_ddb_table.meta.client.transact_write_items.return_value = None

        sample_project.department_id = "dept-new-789"
        sample_project.name = "Moved Project"

        await project_repository.update(sample_project)

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
        project_repository,
        mock_ddb_table,
        sample_project,
    ):
        mock_ddb_table.get_item.return_value = {}

        with pytest.raises(Exception) as exc_info:
            await project_repository.update(sample_project)

        assert "not found" in str(exc_info.value).lower()
