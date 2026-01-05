from typing import Protocol

from app.models.user import UserClaims


class TokenProvider(Protocol):
    """
    TokenProvider interface/protocol
    """

    def generate_token(self, claims: UserClaims) -> str:
        """
        Generates token for input claims
        :returns token string
        """
        ...

    def validate_token(self, token: str) -> UserClaims:
        """
        Validates token string and parses the token claims
        :returns token claims
        """
        ...
