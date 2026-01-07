import uuid
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.interfaces import PasswordHasher, UserRepository, ProjectRepository
from app.models.user import User


class UserService:
    def __init__(
        self,
        password_hasher: PasswordHasher,
        user_repo: UserRepository,
        project_repo: ProjectRepository,
    ):
        self.password_hasher = password_hasher
        self.user_repo = user_repo
        self.project_repo = project_repo

    async def create_user(self, user: User) -> str:
        if not user.password:
            raise AppException(AppErr.CREATE_USER_PASSWORD_REQUIRED)
        hashed_password = self.password_hasher.hash_password(user.password)
        user.password = hashed_password
        user.id = uuid.uuid4().hex
        await self.user_repo.save(user)
        return user.id

    async def update_user(self, user: User) -> None:
        if user.password != "":
            hashed_password = self.password_hasher.hash_password(user.password)
            user.password = hashed_password
        await self.user_repo.update(user)

    async def get_user_by_id(self, user_id: str) -> User:
        user = await self.user_repo.get(user_id)
        if not user:
            raise AppException(AppErr.USER_NOT_FOUND)
        return user

    async def get_all_users(self) -> list[User]:
        return await self.user_repo.get_all()

    async def delete_user(self, curr_user_id: str, user_id: str):
        if curr_user_id == user_id:
            raise AppException(AppErr.CANNOT_DELETE_SELF)
        await self.user_repo.delete(user_id)

    async def get_user_budget(self, user_id: str) -> float:
        user = await self.user_repo.get(user_id)
        if user is None:
            raise AppException(AppErr.USER_NOT_FOUND)

        if user.project_id == "":
            return 0.0

        project = await self.project_repo.get(user.project_id)
        if project is None:
            return 0.0

        return float(project.budget)
