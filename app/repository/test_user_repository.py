import pytest
from app.repository import create_ddb_client, create_ddb_resource
from app.repository.user_repository import UserRepository


@pytest.fixture
def user_repository() -> UserRepository:
    ddb_client = create_ddb_client()
    ddb_resource = create_ddb_resource()
    return UserRepository(ddb_client, ddb_resource, "watch-expense-table")


class TestUserRepository:
    def test_get_all(self, user_repository):
        print(user_repository.get_all())
        # TODO: tests
