from decimal import Decimal
from uuid import uuid4
import pytest
import pytest_asyncio
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.models.department import Department
from app.repository.department_repository import DepartmentRepository


class TestDepartmentRepository:
    @pytest_asyncio.fixture(scope="class")
    async def department_repository(self, ddb_table, table_name):
        return DepartmentRepository(ddb_table, table_name)

    @pytest_asyncio.fixture(scope="class")
    async def department_uuid(self) -> str:
        return uuid4().hex

    @pytest_asyncio.fixture(scope="class")
    async def department(self, department_uuid):
        return Department.model_validate({
            "id": department_uuid,
            "name": "Test Department",
            "budget": Decimal("50000.00"),
        })

    @pytest.mark.asyncio
    async def test_save(self, department_repository, department):
        await department_repository.save(department)

    @pytest.mark.asyncio
    async def test_save_department_already_exists(self, department_repository, department):
        with pytest.raises(AppException) as app_exc:
            await department_repository.save(department)
        assert app_exc.value.err_code == AppErr.DEPARTMENT_ALREADY_EXISTS

    @pytest.mark.asyncio
    async def test_get(self, department_repository, department):
        result = await department_repository.get(department.id)
        assert result is not None
        assert result.id == department.id
        assert result.name == department.name
        assert result.budget == department.budget

    @pytest.mark.asyncio
    async def test_get_non_existent(self, department_repository):
        result = await department_repository.get("non-existent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_update(self, department_repository, department):
        department.name = "Updated Department Name"
        department.budget = Decimal("75000.00")

        await department_repository.update(department)

        result = await department_repository.get(department.id)
        assert result is not None
        assert result.name == "Updated Department Name"
        assert result.budget == Decimal("75000.00")

    @pytest.mark.asyncio
    async def test_update_non_existent(self, department_repository):
        non_existent_department = Department.model_validate({
            "id": "non-existent-id",
            "name": "Ghost Department",
            "budget": Decimal("10000"),
        })
        with pytest.raises(AppException) as app_exc:
            await department_repository.update(non_existent_department)
        assert app_exc.value.err_code == AppErr.NOT_FOUND


class TestDepartmentRepositoryGetAll:
    """Test class for get_all with multiple departments"""

    @pytest_asyncio.fixture(scope="class")
    async def department_repository(self, ddb_table, table_name):
        return DepartmentRepository(ddb_table, table_name)

    @pytest_asyncio.fixture(scope="class")
    async def setup_departments(self, department_repository):
        """Create multiple departments for testing get_all"""
        departments = [
            Department.model_validate({
                "id": uuid4().hex,
                "name": f"Department {i}",
                "budget": Decimal(f"{10000 * (i + 1)}"),
            })
            for i in range(5)
        ]

        for department in departments:
            await department_repository.save(department)

        return departments

    @pytest.mark.asyncio
    async def test_get_all(self, department_repository, setup_departments):
        departments = await department_repository.get_all()

        assert len(departments) >= 5

        department_ids = {dept.id for dept in departments}
        for department in setup_departments:
            assert department.id in department_ids

    @pytest.mark.asyncio
    async def test_get_all_returns_correct_data(self, department_repository, setup_departments):
        departments = await department_repository.get_all()

        test_department = setup_departments[0]
        found_department = next((d for d in departments if d.id == test_department.id), None)

        assert found_department is not None
        assert found_department.name == test_department.name
        assert found_department.budget == test_department.budget
