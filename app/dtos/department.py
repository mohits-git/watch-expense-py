from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, BeforeValidator

from app.dtos.config import FieldAlias, default_model_config
from app.dtos.response import BaseResponse


class DepartmentDTO(BaseModel):
    id: str = FieldAlias("projectId")
    name: str = FieldAlias("name")
    budget: Decimal = FieldAlias("budget")
    created_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = FieldAlias("createdAt", default=0)
    updated_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = FieldAlias("updatedAt", default=0)

    # pydantic config
    model_config = default_model_config()


class CreateDepartmentRequest(BaseModel):
    name: str = FieldAlias("name")
    budget: Decimal = FieldAlias("budget")

    model_config = default_model_config()


class UpdateDepartmentRequest(CreateDepartmentRequest):
    pass


class CreateDepartmentResponse(BaseResponse):
    class CreateDepartmentResponseData(BaseModel):
        id: str

    data: DepartmentDTO

    model_config = default_model_config()


class GetDepartmentResponse(BaseResponse):
    data: DepartmentDTO

    model_config = default_model_config()


class GetDepartmentsResponse(BaseResponse):
    data: list[DepartmentDTO]

    model_config = default_model_config()
