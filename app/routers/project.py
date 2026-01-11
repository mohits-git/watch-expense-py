from typing import Annotated
from fastapi import APIRouter, Depends, Path
from app.dependencies.auth import required_roles
from app.dependencies.services import ProjectServiceInstance
from app.dtos.project import (
    GetProjectResponse,
    GetAllProjectsResponse,
    CreateProjectRequest,
    CreateProjectResponse,
    ProjectDTO,
    UpdateProjectRequest,
)
from app.dtos.response import BaseResponse
from app.models.project import Project
from app.models.user import UserRole

project_router = APIRouter(
    prefix="/admin/projects",
    dependencies=[Depends(required_roles([UserRole.Admin]))],
    tags=["Projects"]
)


@project_router.get("/", response_model=GetAllProjectsResponse)
async def handle_get_all_projects(project_service: ProjectServiceInstance):
    projects = await project_service.get_all_projects()
    return GetAllProjectsResponse(
        status=200,
        message="Projects retrieved successfully",
        data=[ProjectDTO(**project.model_dump()) for project in projects],
    )


@project_router.post("/", response_model=CreateProjectResponse, status_code=201)
async def handle_create_project(
    create_project_request: CreateProjectRequest,
    project_service: ProjectServiceInstance,
):
    project = Project(**create_project_request.model_dump(by_alias=False))
    project_id = await project_service.create_project(project)
    return CreateProjectResponse(
        status=201,
        message="Project created successfully",
        data=CreateProjectResponse.Data(id=project_id),
    )


@project_router.get("/{project_id}", response_model=GetProjectResponse)
async def handle_get_project_by_id(
    project_id: Annotated[str, Path()], project_service: ProjectServiceInstance
):
    project = await project_service.get_project_by_id(project_id)
    return GetProjectResponse(
        status=200,
        message="Project retrieved successfully",
        data=ProjectDTO(**project.model_dump()),
    )


@project_router.put(
    "/{project_id}", response_model=BaseResponse, response_model_exclude_none=True
)
async def handle_update_project(
    project_id: Annotated[str, Path()],
    update_project_request: UpdateProjectRequest,
    project_service: ProjectServiceInstance,
):
    project = Project(**update_project_request.model_dump(by_alias=False))
    project.id = project_id
    await project_service.update_project(project)
    return BaseResponse(status=200, message="Project updated successfully", data=None)
