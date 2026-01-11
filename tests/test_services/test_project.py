from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
import pytest
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.models.project import Project
from app.services.project import ProjectService


class TestProjectService:
    @pytest.fixture
    def mock_project_repo(self):
        repo = MagicMock()
        repo.save = AsyncMock()
        repo.get = AsyncMock()
        repo.get_all = AsyncMock()
        repo.update = AsyncMock()
        return repo

    @pytest.fixture
    def project_service(self, mock_project_repo):
        return ProjectService(mock_project_repo)

    @pytest.fixture
    def sample_project(self):
        return Project.model_validate({
            "id": uuid4().hex,
            "name": "Web Application",
            "description": "Customer portal",
            "budget": Decimal("75000.00"),
            "start_date": 1000000,
            "end_date": 2000000,
            "department_id": "dept-123",
        })

    @pytest.mark.asyncio
    async def test_create_project_success(self, project_service, mock_project_repo):
        project = Project.model_validate({
            "name": "Mobile App",
            "description": "iOS application",
            "budget": Decimal("50000.00"),
            "start_date": 1000000,
            "end_date": 2000000,
            "department_id": "dept-456",
        })

        result = await project_service.create_project(project)

        assert result is not None
        assert len(result) > 0
        assert project.id == result
        mock_project_repo.save.assert_called_once_with(project)

    @pytest.mark.asyncio
    async def test_update_project_success(self, project_service, sample_project, mock_project_repo):
        sample_project.name = "Updated Web Application"

        await project_service.update_project(sample_project)

        mock_project_repo.update.assert_called_once_with(sample_project)

    @pytest.mark.asyncio
    async def test_get_project_by_id_success(self, project_service, sample_project, mock_project_repo):
        mock_project_repo.get.return_value = sample_project

        result = await project_service.get_project_by_id(sample_project.id)

        assert result == sample_project
        mock_project_repo.get.assert_called_once_with(sample_project.id)

    @pytest.mark.asyncio
    async def test_get_project_by_id_not_found(self, project_service, mock_project_repo):
        mock_project_repo.get.return_value = None

        with pytest.raises(AppException) as exc:
            await project_service.get_project_by_id("non-existent-id")

        assert exc.value.err_code == AppErr.NOT_FOUND
        assert "Project not found" in str(exc.value)

    @pytest.mark.asyncio
    async def test_get_all_projects(self, project_service, sample_project, mock_project_repo):
        projects_list = [sample_project]
        mock_project_repo.get_all.return_value = projects_list

        result = await project_service.get_all_projects()

        assert result == projects_list
        mock_project_repo.get_all.assert_called_once()
