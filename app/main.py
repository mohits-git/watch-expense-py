from contextlib import asynccontextmanager
from fastapi import FastAPI
from uvicorn import run

from app.utils.jwt_token_provider import JWTTokenProvider
from app.utils.bcrypt_password_hasher import BcryptPasswordHasher

from app.repository import get_boto3_session
from app.repository.user_repository import UserRepository

from app.services.auth_service import AuthService


@asynccontextmanager
async def lifespan(app: FastAPI):
    global ddb_resource
    session = get_boto3_session()
    async with session.resource("dynamodb") as dynamodb_resource:
        # ddb
        table_name = "watch-expense-table"
        ddb_table = await dynamodb_resource.Table(table_name)
        # repos
        user_repo = UserRepository(ddb_table, table_name)
        # utils
        token_provider = JWTTokenProvider('top-secret')
        password_hasher = BcryptPasswordHasher()
        # services
        auth_service = AuthService(user_repo, token_provider, password_hasher)

        # add to state
        app.state.auth_service = auth_service
        yield
        app.state.ddb_table = None


app = FastAPI(lifespan=lifespan)


def main():
    print("Running server with Uvicorn")
    run(app)


if __name__ == "__main__":
    main()
