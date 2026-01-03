from pydantic import BaseModel
from app.models.expense import RequestStatus
from app.models import default_model_config, FieldAlias


class Advance(BaseModel):
    id: str = FieldAlias("AdvanceID")
    user_id: str = FieldAlias("UserID")
    amount: float = FieldAlias("Amount")
    description: str = FieldAlias("Description")
    purpose: str = FieldAlias("Purpose")
    status: RequestStatus = FieldAlias("Status")
    reconciled_expense_id: str | None = FieldAlias(
        "ReconciledExpenseID", default=None)
    approved_by: str | None = FieldAlias("ApprovedBy", default=None)
    approved_at: int | None = FieldAlias("ApprovedAt", default=None)
    reviewed_by: str | None = FieldAlias("ReviewedBy", default=None)
    reviewed_at: int | None = FieldAlias("ReviewedAt", default=None)
    created_at: int = FieldAlias("CreatedAt")
    updated_at: int = FieldAlias("UpdatedAt")

    # pydantic config
    model_config = default_model_config()


class AdvancesFilterOptions(BaseModel):
    user_id: str
    page: int
    limit: int
    status: RequestStatus


class AdvanceSummary(BaseModel):
    approved: float
    reconciled: float
    pending: float
    rejected: float
