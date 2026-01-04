import pytest
import time
from decimal import Decimal
from app.models.project import Project
from app.repository import create_ddb_client, create_ddb_resource
from app.repository.project_repository import ProjectRepository


@pytest.fixture
def project_repository() -> ProjectRepository:
    ddb_client = create_ddb_client()
    ddb_resource = create_ddb_resource()
    return ProjectRepository(ddb_client, ddb_resource, "watch-expense-table")


class TestProjectRepository:
    def test_get_all(self, project_repository):
        # print(project_repository.get_all())
        # TODO: tests
        pass

    def test_save(self, project_repository):
        # project = Project(
        #     id="d7e4071d-8ca1-4be7-9be3-bce3806f526a",
        #     name="Test Project",
        #     description="Test Description",
        #     budget=Decimal(10000.0),
        #     start_date=int(time.time_ns()//1e6),
        #     end_date=int(time.time_ns()//1e6) + 100000000,
        #     department_id="dep1"
        # )
        # project_repository.save(project)
        pass

    def test_get(self, project_repository):
        # project_id = "d7e4071d-8ca1-4be7-9be3-bce3806f526a"
        # print(project_repository.get(project_id))
        pass

    def test_update(self, project_repository):
        # project = Project(
        #     id="d7e4071d-8ca1-4be7-9be3-bce3806f526a",
        #     name="Testing2 Project Update",
        #     description="Testing2 Description",
        #     budget=Decimal(30000.0),
        #     start_date=int(time.time_ns()//1e6),
        #     end_date=int(time.time_ns()//1e6) + 100000000,
        #     department_id="dep4"
        # )
        # project_repository.update(project)
        # project_id = "d7e4071d-8ca1-4be7-9be3-bce3806f526a"
        # print(project_repository.get(project_id))
        pass
