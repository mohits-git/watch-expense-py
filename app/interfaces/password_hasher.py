from typing import Protocol


class PasswordHasher(Protocol):
    """
    PasswordHasher interface/protocol
    """

    def hash_password(self, password: str) -> str:
        """
        Hashes a input password string
        :returns password hash string
        """
        ...

    def verify_password(self, password_hash: str, password: str) -> bool:
        """
        Verifies the input password to the provided password_hash
        :returns password hash string
        """
        ...
