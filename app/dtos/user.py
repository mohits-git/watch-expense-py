from typing import Annotated
from pydantic import BaseModel, BeforeValidator

from app.dtos.config import default_model_config, FieldAlias
from app.dtos.response import BaseResponse
from app.models.user import UserRole


class UserDTO(BaseModel):
    id: str = FieldAlias("userId")
    employee_id: str = FieldAlias("employeeId")
    name: str = FieldAlias("name")
    email: str = FieldAlias("email")
    role: UserRole = FieldAlias("role")
    project_id: str = FieldAlias("projectId", default="")
    department_id: str = FieldAlias("departmentId", default="")
    created_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = FieldAlias("createdAt", default=0)
    updated_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = FieldAlias("updatedAt", default=0)

    # pydantic config
    model_config = default_model_config()


class GetUserResponse(BaseResponse):
    data: UserDTO


class CreateUserRequest(BaseModel):
    employee_id: str = FieldAlias("employeeId")
    name: str = FieldAlias("name")
    password: str = FieldAlias("password")
    email: str = FieldAlias("email")
    role: UserRole = FieldAlias("role")
    project_id: str = FieldAlias("projectId", default="")
    department_id: str = FieldAlias("departmentId", default="")

    model_config = default_model_config()


class CreateUserResponse(BaseResponse):
    class CreateUserResponseData(BaseModel):
        id: str

    data: CreateUserResponseData


class UpdateUserRequest(CreateUserRequest):
    pass


class GetUserBudgetResponse(BaseResponse):
    class GetUserBudgetResponseData(BaseModel):
        budget: float

    data: GetUserBudgetResponseData
