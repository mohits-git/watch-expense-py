from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field
from app.models.expense import RequestStatus


class Advance(BaseModel):
    id: str = Field(alias="AdvanceID")
    user_id: str = Field(alias="UserID")
    amount: Decimal = Field(alias="Amount")
    description: str = Field(alias="Description")
    purpose: str = Field(alias="Purpose")
    status: RequestStatus = Field(alias="Status")
    reconciled_expense_id: str | None = Field(
        alias="ReconciledExpenseID", default=None)
    approved_by: str | None = Field(alias="ApprovedBy", default=None)
    approved_at: int | None = Field(alias="ApprovedAt", default=None)
    reviewed_by: str | None = Field(alias="ReviewedBy", default=None)
    reviewed_at: int | None = Field(alias="ReviewedAt", default=None)
    created_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = Field(alias="CreatedAt", default=0)
    updated_at: Annotated[int, BeforeValidator(
        lambda x: int(x))] = Field(alias="UpdatedAt", default=0)

    # pydantic config
    model_config = ConfigDict(validate_by_name=True,
                              validate_by_alias=True,
                              serialize_by_alias=False,
                              use_enum_values=True)


class AdvancesFilterOptions(BaseModel):
    user_id: str | None = Field(default=None)
    page: int = Field(default=1)
    limit: int = Field(default=10)
    status: Annotated[RequestStatus | None, BeforeValidator(
        lambda s: None if s == "" else s
    )] = Field(default=None)
    model_config = ConfigDict(validate_by_name=True,
                              validate_by_alias=True,
                              serialize_by_alias=False,
                              use_enum_values=True,
                              extra="ignore")


class AdvanceSummary(BaseModel):
    approved: Decimal
    reconciled: Decimal
    pending: Decimal
    rejected: Decimal
