from decimal import Decimal
import time
import asyncio
from uuid import uuid4
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.interfaces import ExpenseRepository
from app.models.expense import (
    Expense,
    ExpenseSummary,
    ExpensesFilterOptions,
    RequestStatus,
)
from app.models.user import UserClaims, UserRole


class ExpenseService:
    def __init__(self, expense_repo: ExpenseRepository):
        self.expense_repo = expense_repo

    async def get_expense_by_id(
            self, curr_user: UserClaims, expense_id: str) -> Expense:
        expense = await self.expense_repo.get(expense_id)
        if not expense:
            raise AppException(
                AppErr.EXPENSE_NOT_FOUND, f"expense with ID {
                    expense_id} not found"
            )
        if (
            expense.user_id != curr_user.user_id
            and curr_user.role != UserRole.Admin
        ):
            raise AppException(AppErr.FORBIDDEN)
        return expense

    async def create_expense(self, expense: Expense) -> str:
        expense.id = uuid4().hex
        await self.expense_repo.save(expense)
        return expense.id

    async def update_expense(self, curr_user: UserClaims, expense: Expense) -> None:
        existing_expense = await self.expense_repo.get(expense.id)
        if not existing_expense:
            raise AppException(
                AppErr.EXPENSE_NOT_FOUND, f"Expense with ID {
                    expense.id} not found"
            )
        if (
            existing_expense.user_id != curr_user.user_id
            and curr_user.user_id != UserRole.Admin
        ):
            raise AppException(AppErr.FORBIDDEN)

        await self.expense_repo.update(expense)

    async def get_all_expenses(
        self, filter_options: ExpensesFilterOptions
    ) -> tuple[list[Expense], int]:
        expenses, total_count = await self.expense_repo.get_all(filter_options)
        return expenses, total_count

    async def update_expense_status(
        self, curr_user_id: str, expense_id: str, status: RequestStatus
    ) -> None:
        existing_expense = await self.expense_repo.get(expense_id)
        if not existing_expense:
            raise AppException(AppErr.EXPENSE_NOT_FOUND)
        existing_expense.status = status
        if status == RequestStatus.Approved:
            existing_expense.approved_by = curr_user_id
            existing_expense.approved_at = int(time.time())
        if status == RequestStatus.Reviewed:
            existing_expense.reviewed_by = curr_user_id
            existing_expense.reviewed_at = int(time.time())
        await self.expense_repo.update(existing_expense)

    async def get_expense_summary(self, user_id: str) -> ExpenseSummary:
        results = await asyncio.gather(
            self.expense_repo.get_sum(user_id),
            self.expense_repo.get_sum(user_id, RequestStatus.Approved),
            self.expense_repo.get_sum(user_id, RequestStatus.Pending),
            self.expense_repo.get_sum(user_id, RequestStatus.Rejected),
        )
        total, approved, pending, rejected = results

        return ExpenseSummary(
            total_expenses=Decimal(total),
            pending_expense=Decimal(approved),
            reimbursed_expense=Decimal(pending),
            rejected_expense=Decimal(rejected),
        )
