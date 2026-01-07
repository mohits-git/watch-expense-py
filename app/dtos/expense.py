from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from app.dtos.response import BaseResponse
from app.models.expense import RequestStatus


class BillDTO(BaseModel):
    id: str = Field(alias="billId")
    amount: Decimal = Field(alias="amount")
    description: str = Field(alias="description")
    attachment_url: str = Field(alias="attachmentUrl")

    # pydantic config
    model_config = ConfigDict(validate_by_name=True,
                              validate_by_alias=True,
                              serialize_by_alias=True,
                              extra="ignore")


class ExpenseDTO(BaseModel):
    id: str = Field(alias="expenseId")
    user_id: str = Field(alias="userId")
    amount: Decimal = Field(alias="amount")
    description: str = Field(alias="description")
    purpose: str = Field(alias="purpose")
    status: RequestStatus = Field(alias="status")
    is_reconciled: bool = Field(alias="isReconciled")
    approved_by: str | None = Field(alias="approvedBy", default=None)
    approved_at: int | None = Field(alias="approvedAt", default=None)
    reviewed_by: str | None = Field(alias="reviewedBy", default=None)
    reviewed_at: int | None = Field(alias="reviewedAt", default=None)
    created_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = Field(alias="createdAt", default=0)
    updated_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = Field(alias="updatedAt", default=0)

    # pydantic config
    model_config = ConfigDict(validate_by_name=True,
                              validate_by_alias=True,
                              serialize_by_alias=True,
                              use_enum_values=True,
                              extra="ignore")


class CreateBillRequest(BaseModel):
    amount: Decimal
    description: str
    attachment_url: str = Field(alias="attachmentUrl")

    # pydantic config
    model_config = ConfigDict(validate_by_name=True,
                              validate_by_alias=True,
                              serialize_by_alias=True,
                              extra="ignore")


class CreateExpenseRequest(BaseModel):
    amount: Decimal
    description: str
    purpose: str
    bills: list[BillDTO]
    is_reconciled: bool = Field(alias="isReconciled")
    advance_id: str = Field(alias="advanceId")

    # pydantic config
    model_config = ConfigDict(validate_by_name=True,
                              validate_by_alias=True,
                              serialize_by_alias=True,
                              extra="ignore")


class CreateExpenseResponse(BaseResponse):
    class Data(BaseModel):
        id: str

    data: Data


class UpdateExpenseRequest(CreateExpenseRequest):
    pass


class UpdateExpenseStatusRequest(BaseModel):
    status: RequestStatus


class GetExpenseResponse(BaseResponse):
    class Data(BaseModel):
        total_expenses: int = Field(alias="totalExpenses")
        expenses: list[ExpenseDTO] = Field(alias='expenses')

        model_config = ConfigDict(validate_by_name=True,
                                  validate_by_alias=True,
                                  serialize_by_alias=True,
                                  extra="ignore")

    data: Data


class ExpenseSummaryDTO(BaseModel):
    total_expenses: Decimal = Field(alias="totalExpenses")
    pending_expense: Decimal = Field(alias="pendingExpense")
    reimbursed_expense: Decimal = Field(alias="reimbursedExpense")
    rejected_expense: Decimal = Field(alias="rejectedExpense")

    model_config = ConfigDict(validate_by_name=True,
                              validate_by_alias=True,
                              serialize_by_alias=True,
                              extra="ignore")
