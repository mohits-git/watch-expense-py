from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, BeforeValidator
from app.models.config import default_model_config, FieldAlias


class Project(BaseModel):
    id: str = FieldAlias("ProjectID")
    name: str = FieldAlias("Name")
    description: str = FieldAlias("Description")
    budget: Decimal = FieldAlias("Budget")
    start_date: int = FieldAlias("StartDate")
    end_date: int = FieldAlias("EndDate")
    department_id: str = FieldAlias("DepartmentID")
    created_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = FieldAlias("CreatedAt", default=0)
    updated_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = FieldAlias("UpdatedAt", default=0)

    # pydantic config
    model_config = default_model_config()
