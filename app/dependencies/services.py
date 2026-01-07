from typing import Annotated
from fastapi import Depends, Request

from app.services.auth import AuthService
from app.services.user import UserService
from app.services.project import ProjectService
from app.services.department import DepartmentService
from app.services.expense import ExpenseService
from app.services.advance import AdvanceService


def get_auth_service(request: Request) -> AuthService:
    return request.app.state.auth_service


def get_user_service(request: Request) -> UserService:
    return request.app.state.user_service


def get_project_service(request: Request) -> ProjectService:
    return request.app.state.project_service


def get_department_service(request: Request) -> DepartmentService:
    return request.app.state.department_service


def get_expense_service(request: Request) -> ExpenseService:
    return request.app.state.expense_service


def get_advance_service(request: Request) -> AdvanceService:
    return request.app.state.advance_service


AuthServiceInstance = Annotated[AuthService, Depends(get_auth_service)]
UserServiceInstance = Annotated[UserService, Depends(get_user_service)]
ProjectServiceInstance = Annotated[ProjectService, Depends(get_project_service)]
DepartmentServiceInstance = Annotated[DepartmentService, Depends(get_department_service)]
ExpenseServiceInstance = Annotated[ExpenseService, Depends(get_expense_service)]
AdvanceServiceInstance = Annotated[AdvanceService, Depends(get_advance_service)]
