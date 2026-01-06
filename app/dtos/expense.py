from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, BeforeValidator

from app.dtos.config import FieldAlias, default_model_config
from app.dtos.response import BaseResponse
from app.models.expense import RequestStatus


class BillDTO(BaseModel):
    id: str = FieldAlias("billId")
    amount: Decimal = FieldAlias("amount")
    description: str = FieldAlias("description")
    attachment_url: str = FieldAlias("attachmentUrl")

    # pydantic config
    model_config = default_model_config()


class ExpenseDTO(BaseModel):
    id: str = FieldAlias("expenseId")
    user_id: str = FieldAlias("userId")
    amount: Decimal = FieldAlias("amount")
    description: str = FieldAlias("description")
    purpose: str = FieldAlias("purpose")
    status: RequestStatus = FieldAlias("status")
    is_reconciled: bool = FieldAlias("isReconciled")
    approved_by: str | None = FieldAlias("approvedBy", default=None)
    approved_at: int | None = FieldAlias("approvedAt", default=None)
    reviewed_by: str | None = FieldAlias("reviewedBy", default=None)
    reviewed_at: int | None = FieldAlias("reviewedAt", default=None)
    created_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = FieldAlias("createdAt", default=0)
    updated_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = FieldAlias("updatedAt", default=0)

    # pydantic config
    model_config = default_model_config()


class CreateBillRequest(BaseModel):
    amount: Decimal
    description: str
    attachment_url: str = FieldAlias("attachmentUrl")

    # pydantic config
    model_config = default_model_config()


class CreateExpenseRequest(BaseModel):
    amount: Decimal
    description: str
    purpose: str
    is_reconciled: bool = FieldAlias("isReconciled")
    bills: list[BillDTO]
    advance_id = FieldAlias("advanceId")

    model_config = default_model_config()


class CreateExpenseResponse(BaseResponse):
    class CreateExpenseResponseData(BaseModel):
        id: str

    data: CreateExpenseResponseData


class UpdateExpenseRequest(CreateExpenseRequest):
    pass


class UpdateExpenseStatusRequest(BaseModel):
    status: RequestStatus

    model_config = default_model_config()


class GetExpenseResponse(BaseResponse):
    class GetExpenseResponseData(BaseModel):
        total_expenses: int = FieldAlias("totalExpenses")
        expenses: list[ExpenseDTO] = FieldAlias('expenses')

        model_config = default_model_config()

    data: GetExpenseResponseData


class ExpenseSummaryDTO(BaseModel):
    total_expenses: Decimal = FieldAlias("totalExpenses")
    pending_expense: Decimal = FieldAlias("pendingExpense")
    reimbursed_expense: Decimal = FieldAlias("reimbursedExpense")
    rejected_expense: Decimal = FieldAlias("rejectedExpense")

    model_config = default_model_config()
