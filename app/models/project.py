from pydantic import BaseModel
from app.models import default_model_config, FieldAlias


class Project(BaseModel):
    id: str = FieldAlias("ProjectID")
    name: str = FieldAlias("Name")
    description: str = FieldAlias("Description")
    budget: float = FieldAlias("Budget")
    start_date: int = FieldAlias("StartDate")
    end_date: int = FieldAlias("EndDate")
    created_at: int = FieldAlias("CreatedAt")
    updated_at: int = FieldAlias("UpdatedAt")

    # pydantic config
    model_config = default_model_config()
