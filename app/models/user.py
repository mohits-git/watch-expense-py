from typing import Annotated
from pydantic import BaseModel, BeforeValidator
from enum import Enum
from app.models import default_model_config, FieldAlias


class UserRole(str, Enum):
    Admin = "ADMIN"
    Employee = "EMPLOYEE"


class User(BaseModel):
    id: str = FieldAlias("UserID")
    employee_id: str = FieldAlias("EmployeeID")
    name: str = FieldAlias("Name")
    password: str = FieldAlias("PasswordHash")
    email: str = FieldAlias("Email")
    role: UserRole = FieldAlias("Role")
    project_id: str = FieldAlias("ProjectID", default="")
    department_id: str = FieldAlias("DepartmentID", default="")
    created_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = FieldAlias("CreatedAt", default=0)
    updated_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = FieldAlias("UpdatedAt", default=0)

    # pydantic config
    model_config = default_model_config()


class UserClaims(BaseModel):
    id: str = FieldAlias("UserID")
    name: str = FieldAlias("Name")
    email: str = FieldAlias("Email")
    role: UserRole = FieldAlias("Role")

    # pydantic config
    model_config = default_model_config()
