from typing import Annotated
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from app.dtos.response import BaseResponse
from app.models.user import UserRole


class UserDTO(BaseModel):
    id: str = Field(alias="userId")
    employee_id: str = Field(alias="employeeId")
    name: str = Field(alias="name")
    email: str = Field(alias="email")
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
    employee_id: str = Field(alias="employeeId")
    name: str = Field(alias="name")
    password: str = Field(alias="password")
    email: str = Field(alias="email")
    role: UserRole = Field(alias="role")
    project_id: str = Field(alias="projectId", default="")
    department_id: str = Field(alias="departmentId", default="")

    # pydantic config
    model_config = ConfigDict(validate_by_name=True,
                              validate_by_alias=True,
                              serialize_by_alias=True,
                              use_enum_values=True,
                              extra="ignore")


class CreateUserResponseData(BaseModel):
    id: str


class CreateUserResponse(BaseResponse):
    data: CreateUserResponseData


class UpdateUserRequest(CreateUserRequest):
    pass


class GetUserBudgetResponseData(BaseModel):
    budget: float


class GetUserBudgetResponse(BaseResponse):
    data: GetUserBudgetResponseData
