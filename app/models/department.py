from typing import Annotated
from pydantic import BaseModel, BeforeValidator
from app.models import default_model_config, FieldAlias


class Department(BaseModel):
    id: str = FieldAlias("DepartmentID")
    name: str = FieldAlias("Name")
    budget: float = FieldAlias("Budget")
    created_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = FieldAlias("CreatedAt", default=0)
    updated_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = FieldAlias("UpdatedAt", default=0)
    # pydantic config
    model_config = default_model_config()
