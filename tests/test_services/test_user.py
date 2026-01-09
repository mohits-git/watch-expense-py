import unittest

from app.services.user import UserService


class TestUserService(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass

    async def test_create_user(self, user_service: UserService):
        pass

    async def test_update_user(self, user_service: UserService):
        pass
