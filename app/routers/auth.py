from fastapi import APIRouter, status
from app.dependencies.services import AuthServiceInstance
from app.dependencies.auth import AuthTokenHeader
from app.dtos.auth import LoginRequest, LoginResponse
from app.dtos.user import UserDTO


auth_router = APIRouter(prefix="/auth", tags=["Auth"])


@auth_router.post('/login', response_model=LoginResponse)
async def handle_login(login_request: LoginRequest, auth_service: AuthServiceInstance):
    token = await auth_service.login(**login_request.model_dump())
    return LoginResponse(
        status=status.HTTP_200_OK,
        message="Logged In Successfully",
        data=LoginResponse.Data(token=token)
    )


@auth_router.get('/me', response_model=UserDTO)
async def handle_auth_me(token: AuthTokenHeader, auth_service: AuthServiceInstance):
    return await auth_service.get_current_user(token)
