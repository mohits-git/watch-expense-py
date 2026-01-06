import pytest
from app.utils.bcrypt_password_hasher import BcryptPasswordHasher


@pytest.fixture
def bcrypt_pw_hasher():
    return BcryptPasswordHasher(12)


def test_bcrypt_valid_password(bcrypt_pw_hasher: BcryptPasswordHasher):
    password_hash = '$2a$12$zixCEDG2iopBrkQCFrbI0eseyoobCSvN8ajMDCxlfj5aZMdbP2uva'
    password = 'password'
    assert bcrypt_pw_hasher.verify_password(password_hash, password)
