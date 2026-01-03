from pydantic import BaseModel
from enum import Enum
from app.models import default_model_config, FieldAlias


class RequestStatus(Enum):
    Pending = "PENDING"
    Approved = "APPROVED"
    Rejected = "REJECTED"
    Reviewed = "REVIEWED"


class Bill(BaseModel):
    id: str = FieldAlias("BillID")
    amount: float = FieldAlias("Amount")
    description: str = FieldAlias("Description")
    attachment_url: str = FieldAlias("AttachmentURL")

    # pydantic config
    model_config = default_model_config()


class Expense(BaseModel):
    id: str = FieldAlias("ExpenseID")
    user_id: str = FieldAlias("UserID")
    amount: float = FieldAlias("Amount")
    description: str = FieldAlias("Description")
    purpose: str = FieldAlias("Purpose")
    status: RequestStatus = FieldAlias("Status")
    is_reconciled: bool = FieldAlias("IsReconciled")
    approved_by: str | None = FieldAlias("ApprovedBy", default=None)
    approved_at: int | None = FieldAlias("ApprovedAt", default=None)
    reviewed_by: str | None = FieldAlias("ReviewedBy", default=None)
    reviewed_at: int | None = FieldAlias("ReviewedAt", default=None)
    bills: list[Bill] = FieldAlias("Bills", default_factory=list)
    created_at: int = FieldAlias("CreatedAt")
    updated_at: int = FieldAlias("UpdatedAt")

    # pydantic config
    model_config = default_model_config()


class ExpensesFilterOptions(BaseModel):
    user_id: str
    page: int
    limit: int
    status: RequestStatus


class ExpenseSummary(BaseModel):
    total_expenses: float
    pending_expense: float
    reimbursed_expense: float
    rejected_expense: float
