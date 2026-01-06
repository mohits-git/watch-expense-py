from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.interfaces import PasswordHasher, TokenProvider, UserRepository
from app.models.user import User, UserClaims


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        token_provider: TokenProvider,
        password_hasher: PasswordHasher,
    ):
        self._user_repo = user_repo
        self._token_provider = token_provider
        self._password_hasher = password_hasher

    async def login(self, email: str, password: str) -> str:
        """
        handles user login for the input email and password and returns a (jwt) access token
        :returns token_string
        """
        user = await self._user_repo.get_by_email(email)
        if (
            user is None
            or not user.password
            or not self._password_hasher.verify_password(password, user.password)
        ):
            raise AppException(AppErr.INVALID_USER_CREDENTIAL)

        token = self._token_provider.generate_token(
            UserClaims.model_validate(user.model_dump(), extra="ignore")
        )
        return token

    async def get_current_user(self, token: str) -> User:
        user_claims = self._token_provider.validate_token(token)
        user = await self._user_repo.get(user_claims.user_id)
        if user is None:
            raise Exception("Invalid user token")
        user.password = ''
        return user

    def logout(self, token: str) -> None:
        return
