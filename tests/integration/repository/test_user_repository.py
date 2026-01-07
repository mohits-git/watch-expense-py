import pytest
from app.models.user import User, UserRole
from app.repository import get_boto3_session
from app.repository.user_repository import UserRepository
import pytest_asyncio


@pytest_asyncio.fixture
async def user_repository():
    session = get_boto3_session()
    async with session.resource("dynamodb") as ddb_resource:
        ddb_table = await ddb_resource.Table("watch-expense-table")
        yield UserRepository(ddb_table, "watch-expense-table")


class TestUserRepository:
    @pytest.mark.asyncio
    async def test_get_all(self, user_repository: UserRepository):
        print(await user_repository.get_all())
        pass

    @pytest.mark.asyncio
    async def test_get(self, user_repository):
        print(await user_repository.get("a97a4962-dcb9-43a4-aed4-2f5c23a352c0"))
        pass

    @pytest.mark.asyncio
    async def test_get_by_email(self, user_repository):
        print(await user_repository.get_by_email("johntest3@test.com"))
        pass

    @pytest.mark.asyncio
    async def test_save(self, user_repository):
        user = User.model_validate(
            {
                "id": "dddf0940-55ae-4d28-91cf-acbf01c1e7a9",
                "employee_id": "emp5",
                "name": "Testing5 User",
                "password": "hashed_password",
                "email": "johntest5@test.com",
                "role": UserRole.Employee,
                "project_id": "proj1",
                "department_id": "dep1",
            }
        )
        await user_repository.save(user)
        pass

    @pytest.mark.asyncio
    async def test_update(self, user_repository):
        user = User.model_validate({
            "id": "dddf0940-55ae-4d28-91cf-acbf01c1e7a9",
            "employee_id": "emp2",
            "name": "Testing User",
            "password": "hashed_password",
            "email": "johntest5@test.com",
            "role": UserRole.Employee,
            "project_id": "proj2",
            "department_id": "dep2",
        })
        await user_repository.update(user)
        pass
