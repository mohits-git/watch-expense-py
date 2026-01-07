from typing import Annotated
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel

from app.dependencies.services import ExpenseServiceInstance
from app.models.expense import Expense, ExpensesFilterOptions
from app.dtos.expense import (
    CreateExpenseResponse,
    ExpenseDTO,
    GetExpenseResponse,
    GetAllExpensesResponse,
    CreateExpenseRequest,
    UpdateExpenseRequest,
    GetExpenseSummaryResponse,
)
from app.dependencies.auth import AuthenticatedUser, required_roles
from app.models.user import UserRole


expense_router = APIRouter(
    prefix="/expenses", dependencies=[Depends(required_roles([UserRole.Admin]))],
    tags=["Expenses"]
)


@expense_router.get("/", response_model=GetAllExpensesResponse)
async def handle_get_all_expenses(
    filter_options: Annotated[ExpensesFilterOptions, Query()],
    expense_service: ExpenseServiceInstance,
):
    expenses, total_expenses = await expense_service.get_all_expenses(filter_options)
    expenses_dto = [ExpenseDTO(**expense.model_dump()) for expense in expenses]
    return GetAllExpensesResponse(
        status=status.HTTP_200_OK,
        message="Expenses fetched successfully",
        data=GetAllExpensesResponse.Data(
            totalExpenses=total_expenses,
            expenses=expenses_dto,
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


@expense_router.post("/", response_model=CreateExpenseResponse)
async def handle_create_expense(
    create_expense_request: CreateExpenseRequest,
    expense_service: ExpenseServiceInstance,
):
    expense = Expense(**create_expense_request.model_dump(by_alias=False))
    expense_id = await expense_service.create_expense(expense)
    return CreateExpenseResponse(
        status=status.HTTP_201_CREATED,
        message="Expense created successfully",
        data=CreateExpenseResponse.Data(id=expense_id),
    )


@expense_router.put("/{expense_id}", response_model=BaseModel, response_model_exclude_none=True)
async def handle_update_expense(
    curr_user: AuthenticatedUser,
    expense_id: str,
    update_expense_request: UpdateExpenseRequest,
    expense_service: ExpenseServiceInstance,
):
    expense = Expense(**update_expense_request.model_dump(by_alias=False))
    expense.id = expense_id
    await expense_service.update_expense(curr_user, expense)
    return BaseModel(
        status=status.HTTP_200_OK,
        message="Expense updated successfully",
    )


@expense_router.get("/summary", response_model=GetExpenseSummaryResponse)
async def handle_get_expense_summary(
    curr_user: AuthenticatedUser,
    expense_service: ExpenseServiceInstance,
):
    expense_summary = await expense_service.get_expense_summary(curr_user.user_id)
    return GetExpenseSummaryResponse(
        status=status.HTTP_200_OK,
        message="Expense summary fetched successfully",
        data=GetExpenseSummaryResponse.Data(
            **expense_summary.model_dump()
        ),
    )
