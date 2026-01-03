import pytest
from app.models.user import User, UserRole
from app.repository import create_ddb_client
from app.repository.user_repository import UserRepository


@pytest.fixture
def user_repository() -> UserRepository:
    ddb_client = create_ddb_client()
    return UserRepository(ddb_client, "watch-expense-table")


class TestUserRepository:
    def test_save(self, user_repository):
        user_data = User(
            id="",
            employee_id="E123",
            name="John Doe",
            password="hashedpassword",
            email="johntest@test.com",
            role=UserRole.Employee,
            project_id="P123",
            department_id="D123",
            created_at=0,
            updated_at=0)

        user_repository.save(user_data)
