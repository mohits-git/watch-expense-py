from typing import Annotated
from pydantic import BaseModel, BeforeValidator, ConfigDict, EmailStr, Field
from enum import Enum


class UserRole(str, Enum):
    Admin = "ADMIN"
    Employee = "EMPLOYEE"


class User(BaseModel):
    id: str = Field(alias="UserID", default="")
    employee_id: str = Field(alias="EmployeeID")
    name: str = Field(alias="Name")
    password: str = Field(alias="PasswordHash")
    email: EmailStr = Field(alias="Email")
    role: UserRole = Field(alias="Role")
    project_id: str = Field(alias="ProjectID", default="")
    department_id: str = Field(alias="DepartmentID", default="")
    created_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = Field(alias="CreatedAt", default=0)
    updated_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = Field(alias="UpdatedAt", default=0)

    # pydantic config
    model_config = ConfigDict(validate_by_name=True,
                              validate_by_alias=True,
                              serialize_by_alias=False,
                              use_enum_values=True)


class UserClaims(BaseModel):
    user_id: str = Field(alias="id")
    name: str
    email: EmailStr
    role: UserRole

    # pydantic config
    model_config = ConfigDict(validate_by_name=True,
                              validate_by_alias=True,
                              serialize_by_alias=False,
                              use_enum_values=True)
