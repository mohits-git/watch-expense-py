from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, BeforeValidator

from app.dtos.config import FieldAlias, default_model_config
from app.dtos.response import BaseResponse
from app.models.expense import RequestStatus


class AdvanceDTO(BaseModel):
    id: str = FieldAlias("advanceId")
    user_id: str = FieldAlias("userId")
    amount: Decimal = FieldAlias("amount")
    description: str = FieldAlias("description")
    purpose: str = FieldAlias("purpose")
    status: RequestStatus = FieldAlias("status")
    reconciled_expense_id: str | None = FieldAlias(
        "reconciledExpenseId", default=None)
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


class CreateAdvanceRequest(BaseModel):
    amount: Decimal
    description: str
    purpose: str


class CreateAdvanceResponse(BaseResponse):
    class CreateAdvanceResponseData(BaseModel):
        id: str

    data: CreateAdvanceResponseData


class UpdateAdvanceRequest(CreateAdvanceRequest):
    pass


class UpdateAdvanceStatusRequest(BaseModel):
    status: RequestStatus

    model_config = default_model_config()


class GetAdvanceResponse(BaseResponse):
    class GetAdvanceResponseData(BaseModel):
        total_advances: int = FieldAlias("totalAdvances")
        advances: list[AdvanceDTO] = FieldAlias('advances')

        model_config = default_model_config()

    data: GetAdvanceResponseData


class AdvanceSummaryDTO(BaseModel):
    approved: Decimal = FieldAlias("approved")
    reconciled: Decimal = FieldAlias("reconciled")
    pending: Decimal = FieldAlias("pendingReconciliation")
    rejected: Decimal = FieldAlias("rejectedAdvance")

    model_config = default_model_config()
