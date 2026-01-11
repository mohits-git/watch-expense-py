from typing import Annotated
from fastapi import APIRouter, Depends, Path
from app.dependencies.auth import required_roles
from app.dependencies.services import DepartmentServiceInstance
from app.dtos.department import (
    GetDepartmentResponse,
    GetAllDepartmentsResponse,
    CreateDepartmentRequest,
    CreateDepartmentResponse,
    DepartmentDTO,
    UpdateDepartmentRequest,
)
from app.dtos.response import BaseResponse
from app.models.department import Department
from app.models.user import UserRole

department_router = APIRouter(
    prefix="/admin/departments",
    dependencies=[Depends(required_roles([UserRole.Admin]))],
    tags=["Departments"]
)


@department_router.get("/", response_model=GetAllDepartmentsResponse)
async def handle_get_all_departments(department_service: DepartmentServiceInstance):
    departments = await department_service.get_all_departments()
    return GetAllDepartmentsResponse(
        status=200,
        message="Departments retrieved successfully",
        data=[DepartmentDTO(**department.model_dump()) for department in departments],
    )


@department_router.post("/", response_model=CreateDepartmentResponse, status_code=201)
async def handle_create_department(
    create_department_request: CreateDepartmentRequest,
    department_service: DepartmentServiceInstance,
):
    department = Department(**create_department_request.model_dump(by_alias=False))
    department_id = await department_service.create_department(department)
    return CreateDepartmentResponse(
        status=201,
        message="Department created successfully",
        data=CreateDepartmentResponse.Data(id=department_id),
    )


@department_router.get("/{department_id}", response_model=GetDepartmentResponse)
async def handle_get_department_by_id(
    department_id: Annotated[str, Path()], department_service: DepartmentServiceInstance
):
    department = await department_service.get_department_by_id(department_id)
    return GetDepartmentResponse(
        status=200,
        message="Department retrieved successfully",
        data=DepartmentDTO(**department.model_dump()),
    )


@department_router.put(
    "/{department_id}", response_model=BaseResponse, response_model_exclude_none=True
)
async def handle_update_department(
    department_id: Annotated[str, Path()],
    update_department_request: UpdateDepartmentRequest,
    department_service: DepartmentServiceInstance,
):
    department = Department(**update_department_request.model_dump(by_alias=False))
    department.id = department_id
    await department_service.update_department(department)
    return BaseResponse(
        status=200, message="Department updated successfully", data=None
    )
