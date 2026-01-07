from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from app.dtos.response import BaseResponse
from app.models.expense import RequestStatus


class AdvanceDTO(BaseModel):
    id: str = Field(alias="advanceId")
    user_id: str = Field(alias="userId")
    amount: Decimal = Field(alias="amount")
    description: str = Field(alias="description")
    purpose: str = Field(alias="purpose")
    status: RequestStatus = Field(alias="status")
    reconciled_expense_id: str | None = Field(
        alias="reconciledExpenseId", default=None)
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


class CreateAdvanceRequest(BaseModel):
    amount: Decimal
    description: str
    purpose: str


class CreateAdvanceResponse(BaseResponse):
    class Data(BaseModel):
        id: str

    data: Data


class UpdateAdvanceRequest(CreateAdvanceRequest):
    pass


class UpdateAdvanceStatusRequest(BaseModel):
    status: RequestStatus


class GetAdvanceResponse(BaseResponse):
    data: AdvanceDTO


class GetAllAdvancesResponse(BaseResponse):
    class Data(BaseModel):
        total_advances: int = Field(alias="totalAdvances")
        advances: list[AdvanceDTO] = Field(alias='advances')

        # pydantic config
        model_config = ConfigDict(validate_by_name=True,
                                  validate_by_alias=True,
                                  serialize_by_alias=True)

    data: Data


class GetAdvanceSummaryResponse(BaseResponse):
    class Data(BaseModel):
        approved: Decimal = Field(alias="approved")
        reconciled: Decimal = Field(alias="reconciled")
        pending: Decimal = Field(alias="pendingReconciliation")
        rejected: Decimal = Field(alias="rejectedAdvance")
        # pydantic config
        model_config = ConfigDict(validate_by_name=True,
                                  validate_by_alias=True,
                                  serialize_by_alias=True)
    data: Data
