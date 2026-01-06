from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, BeforeValidator

from app.dtos.config import FieldAlias, default_model_config
from app.dtos.response import BaseResponse


class ProjectDTO(BaseModel):
    id: str = FieldAlias("projectId")
    name: str = FieldAlias("name")
    description: str = FieldAlias("description")
    budget: Decimal = FieldAlias("budget")
    start_date: int = FieldAlias("startDate")
    end_date: int = FieldAlias("endDate")
    department_id: str = FieldAlias("departmentId")
    created_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = FieldAlias("createdAt", default=0)
    updated_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = FieldAlias("updatedAt", default=0)

    # pydantic config
    model_config = default_model_config()


class CreateProjectRequest(BaseModel):
    name: str = FieldAlias("name")
    description: str = FieldAlias("description")
    budget: Decimal = FieldAlias("budget")
    start_date: int = FieldAlias("startDate")
    end_date: int = FieldAlias("endDate")
    department_id: str = FieldAlias("departmentId")

    model_config = default_model_config()


class UpdateProjectRequest(CreateProjectRequest):
    pass


class CreateProjectResponse(BaseResponse):
    class CreateProjectResponseData(BaseModel):
        id: str

    data: ProjectDTO

    model_config = default_model_config()


class GetProjectResponse(BaseResponse):
    data: ProjectDTO

    model_config = default_model_config()


class GetProjectsResponse(BaseResponse):
    data: list[ProjectDTO]

    model_config = default_model_config()
