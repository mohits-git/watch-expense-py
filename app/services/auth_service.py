from app.interfaces import PasswordHasher, TokenProvider, UserRepository
from app.models.user import User, UserClaims


class AuthService:
    def __init__(self,
                 user_repo: UserRepository,
                 token_provider: TokenProvider,
                 password_hasher: PasswordHasher):
        self._user_repo = user_repo
        self._token_provider = token_provider
        self._password_hasher = password_hasher

    def login(self, email: str, password: str) -> str:
        """
        handles user login for the input email and password and returns a (jwt) access token
        :returns token_string
        """
        user = self._user_repo.get_by_email(email)
        if user is None:
            raise Exception("Not Found")

        if not self._password_hasher.verify_password(password, user.password):
            raise Exception("Forbidden")

        token = self._token_provider.generate_token(
            UserClaims.model_validate(**user.model_dump(), extra="ignore"))
        return token

    def get_current_user(self, token: str) -> User:
        user_claims = self._token_provider.validate_token(token)
        user = self._user_repo.get(user_claims.user_id)
        if user is None:
            raise Exception("Invalid user token")
        return user

    def logout(self, token: str) -> None:
        return
