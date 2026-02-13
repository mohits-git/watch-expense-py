from typing import Annotated
from fastapi import APIRouter, Depends, Query, status

from app.dependencies.services import ExpenseServiceInstance
from app.dtos.response import BaseResponse
from app.models.expense import Expense, ExpensesFilterOptions
from app.dtos.expense import (
    CreateExpenseResponse,
    ExpenseDTO,
    GetExpenseResponse,
    GetAllExpensesResponse,
    CreateExpenseRequest,
    UpdateExpenseRequest,
    GetExpenseSummaryResponse,
    UpdateExpenseStatusRequest,
)
from app.dependencies.auth import AuthenticatedUser, authenticated_user, required_roles
from app.models.user import UserRole


expense_router = APIRouter(
    prefix="/expenses",
    dependencies=[Depends(authenticated_user)],
    tags=["Expenses"]
)


@expense_router.get("/", response_model=GetAllExpensesResponse)
async def handle_get_all_expenses(
    curr_user: AuthenticatedUser,
    filter_options: Annotated[ExpensesFilterOptions, Query()],
    expense_service: ExpenseServiceInstance,
):
    expenses, total_expenses = await expense_service.get_all_expenses(curr_user, filter_options)
    expenses_dto = [ExpenseDTO(**expense.model_dump()) for expense in expenses]
    return GetAllExpensesResponse(
        status=status.HTTP_200_OK,
        message="Expenses fetched successfully",
        data=GetAllExpensesResponse.Data(
            totalExpenses=total_expenses,
            expenses=expenses_dto,
        ),
    )


@expense_router.post(
    "/",
    response_model=CreateExpenseResponse,
    status_code=201,
    dependencies=[Depends(required_roles([UserRole.Employee]))],
)
async def handle_create_expense(
    curr_user: AuthenticatedUser,
    create_expense_request: CreateExpenseRequest,
    expense_service: ExpenseServiceInstance,
):
    expense = Expense(**create_expense_request.model_dump(by_alias=False, exclude_none=True))
    expense_id = await expense_service.create_expense(curr_user, expense)
    return CreateExpenseResponse(
        status=status.HTTP_201_CREATED,
        message="Expense created successfully",
        data=CreateExpenseResponse.Data(id=expense_id),
    )


@expense_router.get(
    "/summary",
    response_model=GetExpenseSummaryResponse,
)
async def handle_get_expense_summary(
    curr_user: AuthenticatedUser,
    expense_service: ExpenseServiceInstance,
):
    expense_summary = await expense_service.get_expense_summary(curr_user)
    return GetExpenseSummaryResponse(
        status=status.HTTP_200_OK,
        message="Expense summary fetched successfully",
        data=GetExpenseSummaryResponse.Data(
            **expense_summary.model_dump()
        ),
    )


@expense_router.get("/{expense_id}", response_model=GetExpenseResponse)
async def handle_get_expense_by_id(
    curr_user: AuthenticatedUser,
    expense_id: str,
    expense_service: ExpenseServiceInstance,
):
    expense = await expense_service.get_expense_by_id(curr_user, expense_id)
    expense_dto = ExpenseDTO(**expense.model_dump())
    return GetExpenseResponse(
        status=status.HTTP_200_OK,
        message="Expense fetched successfully",
        data=expense_dto,
    )


@expense_router.put(
    "/{expense_id}",
    response_model=BaseResponse,
    response_model_exclude_none=True,
    dependencies=[Depends(required_roles([UserRole.Admin]))],
)
async def handle_update_expense(
    curr_user: AuthenticatedUser,
    expense_id: str,
    update_expense_request: UpdateExpenseRequest,
    expense_service: ExpenseServiceInstance,
):
    expense = Expense(**update_expense_request.model_dump(by_alias=False, exclude_none=True))
    expense.id = expense_id
    await expense_service.update_expense(curr_user, expense)
    return BaseResponse(
        status=status.HTTP_200_OK,
        message="Expense updated successfully",
        data=None,
    )


@expense_router.patch(
    "/{expense_id}",
    response_model=BaseResponse,
    response_model_exclude_none=True,
    dependencies=[Depends(required_roles([UserRole.Admin]))],
)
async def handle_update_status(
        curr_user: AuthenticatedUser,
        expense_id: str,
        data: UpdateExpenseStatusRequest,
        expense_service: ExpenseServiceInstance,
):
    await expense_service.update_expense_status(curr_user, expense_id, data.status)
    return BaseResponse(
        status=status.HTTP_200_OK,
        message="Expense status updated successfully",
        data=None
    )
