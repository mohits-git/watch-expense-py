from typing import Annotated
from fastapi import APIRouter, Depends, Query, status

from app.dependencies.services import AdvanceServiceInstance
from app.dtos.response import BaseResponse
from app.models.advance import Advance, AdvancesFilterOptions
from app.dtos.advance import (
    CreateAdvanceResponse,
    AdvanceDTO,
    GetAdvanceResponse,
    GetAllAdvancesResponse,
    CreateAdvanceRequest,
    UpdateAdvanceRequest,
    GetAdvanceSummaryResponse,
    UpdateAdvanceStatusRequest,
)
from app.dependencies.auth import AuthenticatedUser, authenticated_user, required_roles
from app.models.user import UserRole


advance_router = APIRouter(
    prefix="/advance-request",
    dependencies=[Depends(authenticated_user)],
    tags=["Advances"]
)


@advance_router.get("/", response_model=GetAllAdvancesResponse)
async def handle_get_all_advances(
    curr_user: AuthenticatedUser,
    filter_options: Annotated[AdvancesFilterOptions, Query()],
    advance_service: AdvanceServiceInstance,
):
    advances, total_advances = await advance_service.get_all_advances(
        curr_user, filter_options)
    advances_dto = [AdvanceDTO(**advance.model_dump()) for advance in advances]
    return GetAllAdvancesResponse(
        status=status.HTTP_200_OK,
        message="Advances fetched successfully",
        data=GetAllAdvancesResponse.Data(
            totalAdvances=total_advances,
            advances=advances_dto,
        ),
    )


@advance_router.post(
    "/",
    response_model=CreateAdvanceResponse,
    status_code=201,
    dependencies=[Depends(required_roles([UserRole.Employee]))],
)
async def handle_create_advance(
    create_advance_request: CreateAdvanceRequest,
    curr_user: AuthenticatedUser,
    advance_service: AdvanceServiceInstance,
):
    advance = Advance(**create_advance_request.model_dump(by_alias=False))
    advance_id = await advance_service.create_advance(curr_user, advance)
    return CreateAdvanceResponse(
        status=status.HTTP_201_CREATED,
        message="Advance created successfully",
        data=CreateAdvanceResponse.Data(id=advance_id),
    )


@advance_router.get("/summary", response_model=GetAdvanceSummaryResponse)
async def handle_get_advance_summary(
    curr_user: AuthenticatedUser,
    advance_service: AdvanceServiceInstance,
):
    advance_summary = await advance_service.get_advance_summary(curr_user)
    return GetAdvanceSummaryResponse(
        status=status.HTTP_200_OK,
        message="Advance summary fetched successfully",
        data=GetAdvanceSummaryResponse.Data(
            **advance_summary.model_dump()
        ),
    )


@advance_router.get("/{advance_id}", response_model=GetAdvanceResponse)
async def handle_get_advance_by_id(
    advance_id: str,
    curr_user: AuthenticatedUser,
    advance_service: AdvanceServiceInstance,
):
    advance = await advance_service.get_advance_by_id(curr_user, advance_id)
    advance_dto = AdvanceDTO(**advance.model_dump())
    return GetAdvanceResponse(
        status=status.HTTP_200_OK,
        message="Advance fetched successfully",
        data=advance_dto,
    )


@advance_router.put(
    "/{advance_id}",
    response_model=BaseResponse,
    response_model_exclude_none=True,
)
async def handle_update_advance(
    curr_user: AuthenticatedUser,
    advance_id: str,
    update_advance_request: UpdateAdvanceRequest,
    advance_service: AdvanceServiceInstance,
):
    advance = Advance(**update_advance_request.model_dump(by_alias=False))
    advance.id = advance_id
    await advance_service.update_advance(curr_user, advance)
    return BaseResponse(
        status=status.HTTP_200_OK,
        message="Advance updated successfully",
        data=None
    )


@advance_router.patch(
    "/{advance_id}",
    response_model=BaseResponse,
    response_model_exclude_none=True,
    dependencies=[Depends(required_roles([UserRole.Admin]))],
)
async def handle_update_status(
        curr_user: AuthenticatedUser,
        advance_id: str,
        data: UpdateAdvanceStatusRequest,
        advance_service: AdvanceServiceInstance,
):
    await advance_service.update_advance_status(curr_user, advance_id, data.status)
    return BaseResponse(
        status=status.HTTP_200_OK,
        message="Advance status updated successfully",
        data=None
    )
