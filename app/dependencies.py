from typing import Annotated
from fastapi import Depends, Request
from app.services.auth_service import AuthService


def get_auth_service(request: Request) -> AuthService:
    return request.app.state.auth_service


AuthServiceInstance = Annotated[AuthService, Depends(get_auth_service)]
