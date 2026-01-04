from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, BeforeValidator
from enum import Enum
from app.models import default_model_config, FieldAlias


class RequestStatus(str, Enum):
    Pending = "PENDING"
    Approved = "APPROVED"
    Rejected = "REJECTED"
    Reviewed = "REVIEWED"


class Bill(BaseModel):
    id: str = FieldAlias("BillID")
    amount: Decimal = FieldAlias("Amount")
    description: str = FieldAlias("Description")
    attachment_url: str = FieldAlias("AttachmentURL")

    # pydantic config
    model_config = default_model_config()


class Expense(BaseModel):
    id: str = FieldAlias("ExpenseID")
    user_id: str = FieldAlias("UserID")
    amount: Decimal = FieldAlias("Amount")
    description: str = FieldAlias("Description")
    purpose: str = FieldAlias("Purpose")
    status: RequestStatus = FieldAlias("Status")
    is_reconciled: bool = FieldAlias("IsReconciled")
    approved_by: str | None = FieldAlias("ApprovedBy", default=None)
    approved_at: int | None = FieldAlias("ApprovedAt", default=None)
    reviewed_by: str | None = FieldAlias("ReviewedBy", default=None)
    reviewed_at: int | None = FieldAlias("ReviewedAt", default=None)
    bills: list[Bill] = FieldAlias("Bills", default_factory=list)
    created_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = FieldAlias("CreatedAt", default=0)
    updated_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = FieldAlias("UpdatedAt", default=0)

    # pydantic config
    model_config = default_model_config()


class ExpensesFilterOptions(BaseModel):
    user_id: str
    page: int
    limit: int
    status: RequestStatus


class ExpenseSummary(BaseModel):
    total_expenses: Decimal
    pending_expense: Decimal
    reimbursed_expense: Decimal
    rejected_expense: Decimal
