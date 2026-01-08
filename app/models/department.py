from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


class Department(BaseModel):
    id: str = Field(alias="DepartmentID", default="")
    name: str = Field(alias="Name")
    budget: Decimal = Field(alias="Budget")
    created_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = Field(alias="CreatedAt", default=0)
    updated_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = Field(alias="UpdatedAt", default=0)

    # pydantic config
    model_config = ConfigDict(validate_by_name=True,
                              validate_by_alias=True,
                              serialize_by_alias=False,
                              use_enum_values=True)
