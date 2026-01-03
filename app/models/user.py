from pydantic import BaseModel
from enum import Enum
from app.models import default_model_config, FieldAlias


class UserRole(Enum):
    Admin = "ADMIN"
    Employee = "EMPLOYEE"


class User(BaseModel):
    id: str = FieldAlias("UserID")
    employee_id: str = FieldAlias("EmployeeId")
    name: str = FieldAlias("Name")
    password: str = FieldAlias("PasswordHash")
    email: str = FieldAlias("Email")
    role: UserRole = FieldAlias("Role")
    project_id: str = FieldAlias("ProjectID")
    department_id: str = FieldAlias("DepartmentID")
    created_at: int = FieldAlias("CreatedAt")
    updated_at: int = FieldAlias("UpdatedAt")

    # pydantic config
    model_config = default_model_config()
