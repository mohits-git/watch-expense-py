from decimal import Decimal
import pytest
import pytest_asyncio
from app.models.department import Department
from app.repository import get_boto3_session
from app.repository.department_repository import DepartmentRepository


@pytest_asyncio.fixture
async def department_repository():
    session = get_boto3_session()
    async with session.resource("dynamodb") as ddb_resource:
        ddb_table = await ddb_resource.Table("watch-expense-table")
        yield DepartmentRepository(ddb_table, "watch-expense-table")


class TestDepartmentRepository:
    @pytest.mark.asyncio
    async def test_get_all(self, department_repository):
        print(await department_repository.get_all())
        # TODO: tests
        pass

    @pytest.mark.asyncio
    async def test_save(self, department_repository):
        department = Department.model_validate(
            {
                "id": "37d593c2-d9d2-4171-98de-e06dfb939b01",
                "name": "Test2 Department",
                "budget": Decimal(10000.0),
            }
        )
        await department_repository.save(department)
        pass

    @pytest.mark.asyncio
    async def test_get(self, department_repository):
        dep_id = "d7e4071d-8ca1-4be7-9be3-bce3806f526a"
        print(await department_repository.get(dep_id))
        pass

    @pytest.mark.asyncio
    async def test_update(self, department_repository):
        department = Department.model_validate({
            "id": "d7e4071d-8ca1-4be7-9be3-bce3806f526a",
            "name": "Testing Department",
            "budget": Decimal(20000.0),
        })
        await department_repository.update(department)
        dep_id = "d7e4071d-8ca1-4be7-9be3-bce3806f526a"
        print(await department_repository.get(dep_id))
        pass
