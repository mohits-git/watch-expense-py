from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from app.dtos.response import BaseResponse


class ProjectDTO(BaseModel):
    id: str = Field(alias="projectId")
    name: str = Field(alias="name")
    description: str = Field(alias="description")
    budget: Decimal = Field(alias="budget")
    start_date: int = Field(alias="startDate")
    end_date: int = Field(alias="endDate")
    department_id: str = Field(alias="departmentId")
    created_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = Field(alias="createdAt", default=0)
    updated_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = Field(alias="updatedAt", default=0)

    # pydantic config
    model_config = ConfigDict(validate_by_name=True,
                              validate_by_alias=True,
                              serialize_by_alias=True,
                              extra="ignore")


class CreateProjectRequest(BaseModel):
    name: str = Field(alias="name")
    description: str = Field(alias="description")
    budget: Decimal = Field(alias="budget")
    start_date: int = Field(alias="startDate")
    end_date: int = Field(alias="endDate")
    department_id: str = Field(alias="departmentId")

    # pydantic config
    model_config = ConfigDict(validate_by_name=True,
                              validate_by_alias=True,
                              serialize_by_alias=True,
                              extra="ignore")


class UpdateProjectRequest(CreateProjectRequest):
    pass


class CreateProjectResponse(BaseResponse):
    class Data(BaseModel):
        id: str

    data: Data


class GetProjectResponse(BaseResponse):
    data: ProjectDTO


class GetAllProjectsResponse(BaseResponse):
    data: list[ProjectDTO]
