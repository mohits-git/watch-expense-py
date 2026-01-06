from fastapi import APIRouter

from app.dependencies import AuthServiceInstance
from app.dtos.auth import LoginRequest, LoginResponse


auth_router = APIRouter(prefix="/api/auth")


@auth_router.post('/login', response_model=LoginResponse)
def handle_login(login_request: LoginRequest, auth_service: AuthServiceInstance):
    token = auth_service.login(**login_request.model_dump())
    return LoginResponse(token=token)
