from typing import Annotated
from fastapi import APIRouter, Depends, Path, status
from app.dependencies.auth import AuthenticatedUser, required_roles
from app.dependencies.services import UserServiceInstance
from app.dtos.response import BaseResponse
from app.dtos.user import (
    CreateUserRequest,
    CreateUserResponse,
    GetAllUsersResponse,
    GetUserBudgetResponse,
    GetUserResponse,
    UpdateUserRequest,
    UserDTO,
)
from app.models.user import User, UserRole


user_router = APIRouter(
    prefix="/users",
    dependencies=[Depends(required_roles([UserRole.Employee, UserRole.Admin]))],
    tags=["Users"]
)
_user_admin_only = APIRouter(dependencies=[Depends(required_roles([UserRole.Admin]))])


@user_router.get("/budget", response_model=GetUserBudgetResponse)
async def handle_get_user_budget(
    curr_user: AuthenticatedUser,
    user_service: UserServiceInstance,
):
    budget = await user_service.get_user_budget(curr_user.user_id)
    return GetUserBudgetResponse(
        status=status.HTTP_200_OK,
        message="Fetched user budget successfully",
        data=GetUserBudgetResponse.Data(budget=budget),
    )


@_user_admin_only.get("/", response_model=GetAllUsersResponse)
async def handle_get_all_users(user_service: UserServiceInstance):
    users = await user_service.get_all_users()
    return GetAllUsersResponse(
        status=status.HTTP_200_OK,
        message="Fetched all users successfully",
        data=[UserDTO(**user.model_dump()) for user in users],
    )


@_user_admin_only.post(
    "/", response_model=CreateUserResponse, status_code=status.HTTP_201_CREATED
)
async def handle_create_user(
    user_data: CreateUserRequest,
    user_service: UserServiceInstance,
):
    user = User(**user_data.model_dump(by_alias=False))
    user_id = await user_service.create_user(user)
    return CreateUserResponse(
        status=status.HTTP_201_CREATED,
        message="User created successfully",
        data=CreateUserResponse.Data(id=user_id),
    )


@_user_admin_only.get("/{user_id}", response_model=GetUserResponse)
async def handle_get_user_by_id(
    user_id: Annotated[str, Path()],
    user_service: UserServiceInstance,
):
    user = await user_service.get_user_by_id(user_id)
    return GetUserResponse(
        status=status.HTTP_200_OK,
        message="Fetched user successfully",
        data=UserDTO(**user.model_dump()),
    )


@_user_admin_only.put(
    "/{user_id}",
    response_model=BaseResponse,
    response_model_exclude_none=True,
)
async def handle_update_user(
    user_id: str,
    user_data: UpdateUserRequest,
    user_service: UserServiceInstance,
):
    user_dict = user_data.model_dump(by_alias=False)
    user = User.model_validate({"id": user_id, **user_dict})
    await user_service.update_user(user)
    return BaseResponse(
        status=status.HTTP_200_OK,
        message="User updated successfully",
        data=None,
    )


@_user_admin_only.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def handle_delete_user(
    curr_user: AuthenticatedUser,
    user_id: Annotated[str, Path()],
    user_service: UserServiceInstance,
):
    await user_service.delete_user(curr_user.user_id, user_id)


user_router.include_router(_user_admin_only)
