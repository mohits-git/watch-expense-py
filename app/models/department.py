from pydantic import BaseModel
from app.models import default_model_config, FieldAlias


class Department(BaseModel):
    id: str = FieldAlias("DepartmentID")
    name: str = FieldAlias("Name")
    budget: float = FieldAlias("Budget")
    created_at: int = FieldAlias("CreatedAt")
    updated_at: int = FieldAlias("UpdatedAt")
    # pydantic config
    model_config = default_model_config()
