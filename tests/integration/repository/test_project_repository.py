from decimal import Decimal
import time
import pytest
import pytest_asyncio
from app.models.project import Project
from app.repository import get_boto3_session
from app.repository.project_repository import ProjectRepository


@pytest_asyncio.fixture
async def project_repository():
    session = get_boto3_session()
    async with session.resource("dynamodb") as ddb_resource:
        ddb_table = await ddb_resource.Table("watch-expense-table")
        yield ProjectRepository(ddb_table, "watch-expense-table")


class TestProjectRepository:
    @pytest.mark.asyncio
    async def test_get_all(self, project_repository):
        print(await project_repository.get_all())
        # TODO: tests
        pass

    @pytest.mark.asyncio
    async def test_save(self, project_repository):
        project = Project(
            id="37d593c2-d9d2-4171-98de-e06dfb939b01",
            name="Test Project",
            description="Test Description",
            budget=Decimal(10000.0),
            start_date=int(time.time_ns()//1e6),
            end_date=int(time.time_ns()//1e6) + 100000000,
            department_id="dep1"
        )
        await project_repository.save(project)
        pass

    @pytest.mark.asyncio
    async def test_get(self, project_repository):
        project_id = "d7e4071d-8ca1-4be7-9be3-bce3806f526a"
        print(await project_repository.get(project_id))
        pass

    @pytest.mark.asyncio
    async def test_update(self, project_repository):
        project = Project(
            id="d7e4071d-8ca1-4be7-9be3-bce3806f526a",
            name="Testing2 Project Update",
            description="Testing2 Description",
            budget=Decimal(30000.0),
            start_date=int(time.time_ns()//1e6),
            end_date=int(time.time_ns()//1e6) + 100000000,
            department_id="dep4"
        )
        await project_repository.update(project)
        project_id = "d7e4071d-8ca1-4be7-9be3-bce3806f526a"
        print(await project_repository.get(project_id))
        pass
