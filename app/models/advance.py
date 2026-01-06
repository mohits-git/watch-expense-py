from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, BeforeValidator
from app.models.expense import RequestStatus
from app.models.config import default_model_config, FieldAlias


class Advance(BaseModel):
    id: str = FieldAlias("AdvanceID")
    user_id: str = FieldAlias("UserID")
    amount: Decimal = FieldAlias("Amount")
    description: str = FieldAlias("Description")
    purpose: str = FieldAlias("Purpose")
    status: RequestStatus = FieldAlias("Status")
    reconciled_expense_id: str | None = FieldAlias(
        "ReconciledExpenseID", default=None)
    approved_by: str | None = FieldAlias("ApprovedBy", default=None)
    approved_at: int | None = FieldAlias("ApprovedAt", default=None)
    reviewed_by: str | None = FieldAlias("ReviewedBy", default=None)
    reviewed_at: int | None = FieldAlias("ReviewedAt", default=None)
    created_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = FieldAlias("CreatedAt", default=0)
    updated_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = FieldAlias("UpdatedAt", default=0)

    # pydantic config
    model_config = default_model_config()


class AdvancesFilterOptions(BaseModel):
    user_id: str
    page: int
    limit: int
    status: RequestStatus


class AdvanceSummary(BaseModel):
    approved: Decimal
    reconciled: Decimal
    pending: Decimal
    rejected: Decimal
