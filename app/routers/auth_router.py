from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.dependencies import AuthServiceInstance, AuthTokenHeader
from app.dtos.auth import LoginRequest, LoginResponse
from app.models.user import User


auth_router = APIRouter(prefix="/auth")


@auth_router.post('/login', response_model=LoginResponse)
async def handle_login(login_request: LoginRequest, auth_service: AuthServiceInstance):
    token = await auth_service.login(**login_request.model_dump())
    return LoginResponse(token=token)


@auth_router.post('/me', response_model=User)
async def handle_auth_me(token: AuthTokenHeader, auth_service: AuthServiceInstance):
    user = await auth_service.get_current_user(token)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=user.model_dump(mode='json', exclude_none=True)
    )
