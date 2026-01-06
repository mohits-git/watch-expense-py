from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field
from enum import Enum


class RequestStatus(str, Enum):
    Pending = "PENDING"
    Approved = "APPROVED"
    Rejected = "REJECTED"
    Reviewed = "REVIEWED"


class Bill(BaseModel):
    id: str = Field(alias="BillID")
    amount: Decimal = Field(alias="Amount")
    description: str = Field(alias="Description")
    attachment_url: str = Field(alias="AttachmentURL")

    # pydantic config
    model_config = ConfigDict(validate_by_name=True,
                              validate_by_alias=True,
                              serialize_by_alias=False,
                              use_enum_values=True)


class Expense(BaseModel):
    id: str = Field(alias="ExpenseID")
    user_id: str = Field(alias="UserID")
    amount: Decimal = Field(alias="Amount")
    description: str = Field(alias="Description")
    purpose: str = Field(alias="Purpose")
    status: RequestStatus = Field(alias="Status")
    is_reconciled: bool = Field(alias="IsReconciled")
    approved_by: str | None = Field(alias="ApprovedBy", default=None)
    approved_at: int | None = Field(alias="ApprovedAt", default=None)
    reviewed_by: str | None = Field(alias="ReviewedBy", default=None)
    reviewed_at: int | None = Field(alias="ReviewedAt", default=None)
    bills: list[Bill] = Field(alias="Bills", default_factory=list)
    created_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = Field(alias="CreatedAt", default=0)
    updated_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = Field(alias="UpdatedAt", default=0)

    # pydantic config
    model_config = ConfigDict(validate_by_name=True,
                              validate_by_alias=True,
                              serialize_by_alias=False,
                              use_enum_values=True)


class ExpensesFilterOptions(BaseModel):
    user_id: str
    page: int
    limit: int
    status: RequestStatus | None


class ExpenseSummary(BaseModel):
    total_expenses: Decimal
    pending_expense: Decimal
    reimbursed_expense: Decimal
    rejected_expense: Decimal
