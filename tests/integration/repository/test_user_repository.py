import pytest
from app.models.user import User, UserRole
from app.repository import create_ddb_resource
from app.repository.user_repository import UserRepository


@pytest.fixture
def user_repository() -> UserRepository:
    ddb_resource = create_ddb_resource()
    return UserRepository(ddb_resource, "watch-expense-table")


class TestUserRepository:
    def test_get_all(self, user_repository):
        # print(user_repository.get_all())
        # TODO: tests
        pass

    def test_get(self, user_repository):
        # print(user_repository.get("a97a4962-dcb9-43a4-aed4-2f5c23a352c0"))
        pass

    def test_get_by_email(self, user_repository):
        # print(user_repository.get_by_email("johntest3@test.com"))
        pass

    def test_save(self, user_repository):
        # user = User(
        #     id="a97a4962-dcb9-43a4-aed4-2f5c23a352c0",
        #     employee_id="emp1",
        #     name="Testing User",
        #     password="hashed_password",
        #     email="johntest2@test.com",
        #     role=UserRole.Employee,
        #     project_id="proj1",
        #     department_id="dep1",
        # )
        # user_repository.save(user)
        pass

    def test_update(self, user_repository):
        # user = User(
        #     id="a97a4962-dcb9-43a4-aed4-2f5c23a352c0",
        #     employee_id="emp2",
        #     name="Testing User",
        #     password="hashed_password",
        #     email="johntest3@test.com",
        #     role=UserRole.Employee,
        #     project_id="proj2",
        #     department_id="dep2",
        # )
        # user_repository.update(user)
        pass
