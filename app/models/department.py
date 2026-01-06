from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, BeforeValidator
from app.models.config import default_model_config, FieldAlias


class Department(BaseModel):
    id: str = FieldAlias("DepartmentID")
    name: str = FieldAlias("Name")
    budget: Decimal = FieldAlias("Budget")
    created_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = FieldAlias("CreatedAt", default=0)
    updated_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = FieldAlias("UpdatedAt", default=0)
    # pydantic config
    model_config = default_model_config()
