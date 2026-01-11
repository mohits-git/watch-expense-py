import pytest
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.infra.bcrypt_password_hasher import BcryptPasswordHasher


class TestBcryptPasswordHasher:
    @pytest.fixture
    def password_hasher(self):
        return BcryptPasswordHasher(cost=12)

    def test_hash_password_creates_valid_hash(self, password_hasher):
        password = "test_password_123"
        hashed = password_hasher.hash_password(password)

        assert hashed is not None
        assert len(hashed) > 0
        assert hashed.startswith("$2")

    def test_hash_password_different_hashes_for_same_password(self, password_hasher):
        password = "same_password"
        hash1 = password_hasher.hash_password(password)
        hash2 = password_hasher.hash_password(password)

        assert hash1 != hash2

    def test_hash_password_with_special_characters(self, password_hasher):
        password = "p@ssw0rd!#$%^&*()"
        hashed = password_hasher.hash_password(password)

        assert hashed is not None
        assert password_hasher.verify_password(hashed, password)

    def test_hash_password_with_unicode(self, password_hasher):
        password = "пароль123"
        hashed = password_hasher.hash_password(password)

        assert hashed is not None
        assert password_hasher.verify_password(hashed, password)

    def test_hash_password_empty_string(self, password_hasher):
        password = ""
        hashed = password_hasher.hash_password(password)

        assert hashed is not None
        assert password_hasher.verify_password(hashed, password)

    def test_hash_password_long_password(self, password_hasher):
        password = "a" * 200
        with pytest.raises(AppException) as excinfo:
            password_hasher.hash_password(password)
        assert excinfo.value.err_code == AppErr.PASSWORD_TOO_LONG

    def test_verify_password_correct_password(self, password_hasher):
        password = "correct_password"
        hashed = password_hasher.hash_password(password)

        assert password_hasher.verify_password(hashed, password) is True

    def test_verify_password_incorrect_password(self, password_hasher):
        password = "correct_password"
        hashed = password_hasher.hash_password(password)

        assert password_hasher.verify_password(hashed, "wrong_password") is False

    def test_verify_password_with_known_hash(self, password_hasher):
        known_hash = "$2a$12$zixCEDG2iopBrkQCFrbI0eseyoobCSvN8ajMDCxlfj5aZMdbP2uva"

        assert password_hasher.verify_password(known_hash, "password") is True
        assert password_hasher.verify_password(known_hash, "wrong") is False

    def test_verify_password_empty_strings(self, password_hasher):
        empty_password = ""
        hashed = password_hasher.hash_password(empty_password)

        assert password_hasher.verify_password(hashed, "") is True
        assert password_hasher.verify_password(hashed, "not_empty") is False
