from pydantic import BaseModel
from app.dtos.response import BaseResponse
from app.dtos.user import UserDTO


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseResponse):
    class Data(BaseModel):
        token: str
    data: Data


class GetAuthMeResponse(BaseResponse):
    data: UserDTO
