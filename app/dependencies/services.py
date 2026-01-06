from typing import Annotated
from fastapi import Depends, Request

from app.services.auth import AuthService
from app.services.user import UserService


def get_auth_service(request: Request) -> AuthService:
    return request.app.state.auth_service


def get_user_service(request: Request) -> UserService:
    return request.app.state.user_service


AuthServiceInstance = Annotated[AuthService, Depends(get_auth_service)]
UserServiceInstance = Annotated[UserService, Depends(get_user_service)]
