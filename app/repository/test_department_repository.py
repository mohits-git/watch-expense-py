import pytest
from app.repository import create_ddb_client, create_ddb_resource
from app.repository.department_repository import DepartmentRepository


@pytest.fixture
def department_repository() -> DepartmentRepository:
    ddb_client = create_ddb_client()
    ddb_resource = create_ddb_resource()
    return DepartmentRepository(ddb_client, ddb_resource, "watch-expense-table")


class TestDepartmentRepository:
    def test_get_all(self, department_repository):
        # print(department_repository.get_all())
        # TODO: tests
        pass

    def test_save(self, department_repository):
        # department = Department(
        #     id="d7e4071d-8ca1-4be7-9be3-bce3806f526a",
        #     name="Test Department",
        #     budget=Decimal(10000.0),
        # )
        # department_repository.save(department)
        pass

    def test_get(self, department_repository):
        # dep_id = "d7e4071d-8ca1-4be7-9be3-bce3806f526a"
        # print(department_repository.get(dep_id))
        pass

    def test_update(self, department_repository):
        # department = Department(
        #     id="d7e4071d-8ca1-4be7-9be3-bce3806f526a",
        #     name="Testing Department",
        #     budget=Decimal(20000.0),
        # )
        # department_repository.update(department)
        # dep_id = "d7e4071d-8ca1-4be7-9be3-bce3806f526a"
        # print(department_repository.get(dep_id))
        pass
