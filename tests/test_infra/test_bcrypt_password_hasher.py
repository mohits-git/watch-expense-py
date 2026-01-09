import unittest
from app.infra.bcrypt_password_hasher import BcryptPasswordHasher


class TestBcryptValidPassword(unittest.TestCase):
    def setUp(self):
        self._bcrypt_password_hasher = BcryptPasswordHasher(12)

    def test_verify_password(self):
        valid_password_hash = '$2a$12$zixCEDG2iopBrkQCFrbI0eseyoobCSvN8ajMDCxlfj5aZMdbP2uva'
        password = 'password'
        self.assertTrue(self._bcrypt_password_hasher.verify_password(
            valid_password_hash, password))

    def test_hash_password(self):
        original_password = "password"
        hashed_password = self._bcrypt_password_hasher.hash_password(
            original_password)
        self.assertTrue(self._bcrypt_password_hasher.verify_password(
            hashed_password, original_password))
