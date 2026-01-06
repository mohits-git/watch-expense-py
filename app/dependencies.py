from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Header, Request, status
from app.repository.user_repository import UserRepository
from app.repository import get_boto3_session
from app.services.auth import AuthService
from app.utils.bcrypt_password_hasher import BcryptPasswordHasher
from app.utils.jwt_token_provider import JWTTokenProvider


def get_auth_service(request: Request) -> AuthService:
    return request.app.state.auth_service


def get_auth_token(authorization: Annotated[str | None, Header()]) -> str:
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized")
    try:
        token = authorization.split(' ', 2)[1]
        return token
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized")


AuthServiceInstance = Annotated[AuthService, Depends(get_auth_service)]
AuthTokenHeader = Annotated[str, Depends(get_auth_token)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    global ddb_resource
    session = get_boto3_session()
    try:
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
            auth_service = AuthService(
                user_repo, token_provider, password_hasher)

            # add to state
            app.state.auth_service = auth_service
            yield
    except Exception as e:
        print("Error while starting up the server: ", e)
