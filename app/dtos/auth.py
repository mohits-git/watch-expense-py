from pydantic import BaseModel, EmailStr
from app.dtos.response import BaseResponse
from app.dtos.user import UserDTO


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseResponse):
    class Data(BaseModel):
        token: str
    data: Data


class GetAuthMeResponse(BaseResponse):
    data: UserDTO
