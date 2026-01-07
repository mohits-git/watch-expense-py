from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from app.dtos.response import BaseResponse


class DepartmentDTO(BaseModel):
    id: str = Field(alias="projectId")
    name: str = Field(alias="name")
    budget: Decimal = Field(alias="budget")
    created_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = Field(alias="createdAt", default=0)
    updated_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = Field(alias="updatedAt", default=0)

    # pydantic config
    model_config = ConfigDict(validate_by_name=True,
                              validate_by_alias=True,
                              serialize_by_alias=True,
                              use_enum_values=True,
                              extra="ignore")


class CreateDepartmentRequest(BaseModel):
    name: str = Field(alias="name")
    budget: Decimal = Field(alias="budget")

    model_config = ConfigDict(validate_by_name=True,
                              validate_by_alias=True,
                              serialize_by_alias=True,
                              extra="ignore")


class UpdateDepartmentRequest(CreateDepartmentRequest):
    pass


class CreateDepartmentResponse(BaseResponse):
    class Data(BaseModel):
        id: str

    data: Data


class GetDepartmentResponse(BaseResponse):
    data: DepartmentDTO


class GetAllDepartmentsResponse(BaseResponse):
    data: list[DepartmentDTO]
