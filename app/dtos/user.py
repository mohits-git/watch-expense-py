from typing import Annotated
from pydantic import BaseModel, BeforeValidator, ConfigDict, EmailStr, Field

from app.dtos.response import BaseResponse
from app.models.user import UserRole


class UserDTO(BaseModel):
    id: str = Field(alias="id")
    employee_id: str = Field(alias="employeeId")
    name: str = Field(alias="name")
    email: EmailStr = Field(alias="email")
    role: UserRole = Field(alias="role")
    project_id: str = Field(alias="projectId", default="")
    department_id: str = Field(alias="departmentId", default="")
    created_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = Field(alias="createdAt", default=0)
    updated_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = Field(alias="updatedAt", default=0)

    # pydantic config
    model_config = ConfigDict(validate_by_name=True,
                              validate_by_alias=True,
                              serialize_by_alias=True,
                              use_enum_values=True,
                              extra="ignore")


class GetUserResponse(BaseResponse):
    data: UserDTO


class GetAllUsersResponse(BaseResponse):
    data: list[UserDTO]


class CreateUserRequest(BaseModel):
    employee_id: str = Field(alias="employeeId", max_length=20)
    name: str = Field(alias="name", max_length=100)
    password: str = Field(alias="password", max_length=72)
    email: EmailStr = Field(alias="email", max_length=50)
    role: UserRole = Field(alias="role")
    project_id: str = Field(alias="projectId", default="")
    department_id: str = Field(alias="departmentId", default="")

    # pydantic config
    model_config = ConfigDict(validate_by_name=True,
                              validate_by_alias=True,
                              serialize_by_alias=True,
                              use_enum_values=True,
                              extra="ignore")


class CreateUserResponse(BaseResponse):
    class Data(BaseModel):
        id: str

    data: Data


class UpdateUserRequest(CreateUserRequest):
    password: str = Field(default="", max_length=72)


class GetUserBudgetResponse(BaseResponse):
    class Data(BaseModel):
        budget: float

    data: Data
