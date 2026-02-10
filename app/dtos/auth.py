from pydantic import BaseModel, EmailStr, Field
from app.dtos.response import BaseResponse
from app.dtos.user import UserDTO


class LoginRequest(BaseModel):
    email: EmailStr = Field(max_length=50)
    password: str = Field(max_length=72)


class LoginResponse(BaseResponse):
    class Data(BaseModel):
        token: str
    data: Data


class GetAuthMeResponse(BaseResponse):
    data: UserDTO
