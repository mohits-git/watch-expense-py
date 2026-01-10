from decimal import Decimal
import time
from uuid import uuid4
import pytest
import pytest_asyncio
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.models.project import Project
from app.repository.project_repository import ProjectRepository


class TestProjectRepository:
    @pytest_asyncio.fixture(scope="class")
    async def project_repository(self, ddb_table, table_name):
        return ProjectRepository(ddb_table, table_name)

    @pytest_asyncio.fixture(scope="class")
    async def department_id(self) -> str:
        return uuid4().hex

    @pytest_asyncio.fixture(scope="class")
    async def project_uuid(self) -> str:
        return uuid4().hex

    @pytest_asyncio.fixture(scope="class")
    async def project(self, project_uuid, department_id):
        current_time = int(time.time_ns() // 1e6)
        return Project.model_validate({
            "id": project_uuid,
            "name": "Test Project",
            "description": "Test Description",
            "budget": Decimal("10000.00"),
            "start_date": current_time,
            "end_date": current_time + 100000000,
            "department_id": department_id,
        })

    @pytest.mark.asyncio
    async def test_save(self, project_repository, project):
        await project_repository.save(project)

    @pytest.mark.asyncio
    async def test_save_project_already_exists(self, project_repository, project):
        with pytest.raises(AppException) as app_exc:
            await project_repository.save(project)
        assert app_exc.value.err_code == AppErr.PROJECT_ALREADY_EXISTS

    @pytest.mark.asyncio
    async def test_get(self, project_repository, project):
        result = await project_repository.get(project.id)
        assert result is not None
        assert result.id == project.id
        assert result.name == project.name
        assert result.description == project.description
        assert result.budget == project.budget
        assert result.start_date == project.start_date
        assert result.end_date == project.end_date
        assert result.department_id == project.department_id

    @pytest.mark.asyncio
    async def test_get_non_existent(self, project_repository):
        result = await project_repository.get("non-existent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_update(self, project_repository, project):
        project.name = "Updated Project Name"
        project.description = "Updated Description"
        project.budget = Decimal("20000.00")

        await project_repository.update(project)

        result = await project_repository.get(project.id)
        assert result is not None
        assert result.name == "Updated Project Name"
        assert result.description == "Updated Description"
        assert result.budget == Decimal("20000.00")

    @pytest.mark.asyncio
    async def test_update_with_department_change(self, project_repository, project):
        old_department_id = project.department_id
        new_department_id = uuid4().hex
        project.department_id = new_department_id
        project.name = "Moved Project"

        await project_repository.update(project)

        result = await project_repository.get(project.id)
        assert result is not None
        assert result.department_id == new_department_id
        assert result.name == "Moved Project"
        assert result.id == project.id

    @pytest.mark.asyncio
    async def test_update_non_existent(self, project_repository, department_id):
        current_time = int(time.time_ns() // 1e6)
        non_existent_project = Project.model_validate({
            "id": "non-existent-id",
            "name": "Ghost Project",
            "description": "Does not exist",
            "budget": Decimal("5000"),
            "start_date": current_time,
            "end_date": current_time + 100000000,
            "department_id": department_id,
        })
        with pytest.raises(Exception) as exc:
            await project_repository.update(non_existent_project)
        assert "not found" in str(exc.value).lower()


class TestProjectRepositoryGetAll:
    """Test class for get_all with multiple projects"""

    @pytest_asyncio.fixture(scope="class")
    async def project_repository(self, ddb_table, table_name):
        return ProjectRepository(ddb_table, table_name)

    @pytest_asyncio.fixture(scope="class")
    async def department_id(self) -> str:
        return uuid4().hex

    @pytest_asyncio.fixture(scope="class")
    async def setup_projects(self, project_repository, department_id):
        """Create multiple projects for testing get_all"""
        current_time = int(time.time_ns() // 1e6)
        projects = [
            Project.model_validate({
                "id": uuid4().hex,
                "name": f"Project {i}",
                "description": f"Description {i}",
                "budget": Decimal(f"{10000 * (i + 1)}"),
                "start_date": current_time,
                "end_date": current_time + 100000000,
                "department_id": department_id if i % 2 == 0 else uuid4().hex,
            })
            for i in range(5)
        ]

        for project in projects:
            await project_repository.save(project)

        return projects

    @pytest.mark.asyncio
    async def test_get_all(self, project_repository, setup_projects):
        projects = await project_repository.get_all()

        assert len(projects) >= 5

        project_ids = {project.id for project in projects}
        for project in setup_projects:
            assert project.id in project_ids

    @pytest.mark.asyncio
    async def test_get_all_returns_correct_data(self, project_repository, setup_projects):
        projects = await project_repository.get_all()

        test_project = setup_projects[0]
        found_project = next((p for p in projects if p.id == test_project.id), None)

        assert found_project is not None
        assert found_project.name == test_project.name
        assert found_project.description == test_project.description
        assert found_project.budget == test_project.budget
        assert found_project.start_date == test_project.start_date
        assert found_project.end_date == test_project.end_date
        assert found_project.department_id == test_project.department_id
