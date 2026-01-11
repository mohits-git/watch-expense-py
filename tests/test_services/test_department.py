from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
import pytest
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.models.department import Department
from app.services.department import DepartmentService


class TestDepartmentService:
    @pytest.fixture
    def mock_department_repo(self):
        repo = MagicMock()
        repo.save = AsyncMock()
        repo.get = AsyncMock()
        repo.get_all = AsyncMock()
        repo.update = AsyncMock()
        return repo

    @pytest.fixture
    def department_service(self, mock_department_repo):
        return DepartmentService(mock_department_repo)

    @pytest.fixture
    def sample_department(self):
        return Department.model_validate({
            "id": uuid4().hex,
            "name": "Engineering",
            "budget": Decimal("100000.00"),
        })

    @pytest.mark.asyncio
    async def test_create_department_success(self, department_service, mock_department_repo):
        department = Department.model_validate({
            "name": "Sales",
            "budget": Decimal("50000.00"),
        })

        result = await department_service.create_department(department)

        assert result is not None
        assert len(result) > 0
        assert department.id == result
        mock_department_repo.save.assert_called_once_with(department)

    @pytest.mark.asyncio
    async def test_update_department_success(self, department_service, sample_department, mock_department_repo):
        sample_department.name = "Updated Engineering"

        await department_service.update_department(sample_department)

        mock_department_repo.update.assert_called_once_with(sample_department)

    @pytest.mark.asyncio
    async def test_get_department_by_id_success(self, department_service, sample_department, mock_department_repo):
        mock_department_repo.get.return_value = sample_department

        result = await department_service.get_department_by_id(sample_department.id)

        assert result == sample_department
        mock_department_repo.get.assert_called_once_with(sample_department.id)

    @pytest.mark.asyncio
    async def test_get_department_by_id_not_found(self, department_service, mock_department_repo):
        mock_department_repo.get.return_value = None

        with pytest.raises(AppException) as exc:
            await department_service.get_department_by_id("non-existent-id")

        assert exc.value.err_code == AppErr.NOT_FOUND
        assert "Department not found" in str(exc.value)

    @pytest.mark.asyncio
    async def test_get_all_departments(self, department_service, sample_department, mock_department_repo):
        departments_list = [sample_department]
        mock_department_repo.get_all.return_value = departments_list

        result = await department_service.get_all_departments()

        assert result == departments_list
        mock_department_repo.get_all.assert_called_once()
