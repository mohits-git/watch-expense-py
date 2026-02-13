from decimal import Decimal
import time
import asyncio
from uuid import uuid4
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.interfaces import (
    ExpenseRepository,
    AdvanceRepository,
    UserRepository,
    NotificationService,
)
from app.models.expense import (
    Expense,
    ExpenseSummary,
    ExpensesFilterOptions,
    RequestStatus,
)
from app.models.notification import EventType, Notification
from app.models.user import UserClaims, UserRole


class ExpenseService:
    def __init__(
            self,
            expense_repo: ExpenseRepository,
            advance_repo: AdvanceRepository,
            user_repo: UserRepository,
            notification_service: NotificationService):
        self.expense_repo = expense_repo
        self.advance_repo = advance_repo
        self.user_repo = user_repo
        self.notification_service = notification_service

    async def get_expense_by_id(
            self, curr_user: UserClaims, expense_id: str) -> Expense:
        expense = await self.expense_repo.get(expense_id)
        if not expense:
            raise AppException(AppErr.NOT_FOUND, "Expense not found")
        if (
            expense.user_id != curr_user.user_id
            and curr_user.role != UserRole.Admin
        ):
            raise AppException(AppErr.FORBIDDEN)
        return expense

    async def create_expense(self, curr_user: UserClaims, expense: Expense) -> str:
        expense.id = uuid4().hex
        expense.user_id = curr_user.user_id
        expense.status = RequestStatus.Pending
        expense.is_reconciled = bool(expense.advance_id)
        if expense.advance_id:
            existing_advance = await self.advance_repo.get(expense.advance_id)
            if not existing_advance:
                raise AppException(AppErr.INVALID_EXPENSE_RECONCILE_ADVANCE)
            if existing_advance.user_id != curr_user.user_id:
                raise AppException(AppErr.EXPENSE_RECONCILE_PERMISSION_DENIED)
            existing_advance.reconciled_expense_id = expense.id
            await asyncio.gather(self.expense_repo.save(expense),
                                 self.advance_repo.update(existing_advance))
        else:
            await self.expense_repo.save(expense)
        return expense.id

    async def update_expense(self, curr_user: UserClaims, expense: Expense) -> None:
        existing_expense = await self.expense_repo.get(expense.id)
        if not existing_expense:
            raise AppException(AppErr.NOT_FOUND, "Expense not found")
        if (
            existing_expense.user_id != curr_user.user_id
            and curr_user.user_id != UserRole.Admin
        ):
            raise AppException(AppErr.FORBIDDEN)

        await self.expense_repo.update(expense)

    async def get_all_expenses(
        self,
        curr_user: UserClaims,
        filter_options: ExpensesFilterOptions
    ) -> tuple[list[Expense], int]:
        if curr_user.role != UserRole.Admin:
            filter_options.user_id = curr_user.user_id
        expenses, total_count = await self.expense_repo.get_all(filter_options)
        return expenses, total_count

    async def _send_status_update_notification(self, expense: Expense):
        user = await self.user_repo.get(expense.user_id)
        if not user:
            return

        notification = Notification(
            event_type=EventType.EXPENSE_APPROVED,
            user=Notification.User(
                name=user.name,
                email=user.email,
            ),
            expense=Notification.Expense(
                expense_id=expense.id,
                purpose=expense.purpose,
                amount=expense.amount,
            ), advance=None)

        if expense.status == RequestStatus.Rejected:
            notification.event_type = EventType.EXPENSE_REJECTED

        await self.notification_service.send_notification(notification)

    async def update_expense_status(
        self, curr_user: UserClaims, expense_id: str, status: RequestStatus
    ) -> None:
        existing_expense = await self.expense_repo.get(expense_id)
        if not existing_expense:
            raise AppException(AppErr.NOT_FOUND, "Expense not found")

        existing_expense.status = status
        if status == RequestStatus.Approved:
            existing_expense.approved_by = curr_user.user_id
            existing_expense.approved_at = int(time.time())
        if status == RequestStatus.Reviewed:
            existing_expense.reviewed_by = curr_user.user_id
            existing_expense.reviewed_at = int(time.time())

        await self.expense_repo.update(existing_expense)

        await self._send_status_update_notification(existing_expense)

    async def get_expense_summary(self, curr_user: UserClaims) -> ExpenseSummary:
        user_id = ""
        if curr_user.role != UserRole.Admin:
            user_id = curr_user.user_id
        results = await asyncio.gather(
            self.expense_repo.get_sum(user_id),
            self.expense_repo.get_sum(user_id, RequestStatus.Approved),
            self.expense_repo.get_sum(user_id, RequestStatus.Pending),
            self.expense_repo.get_sum(user_id, RequestStatus.Rejected),
        )
        total, approved, pending, rejected = results

        return ExpenseSummary(
            total_expense=Decimal(total),
            pending_expense=Decimal(pending),
            reimbursed_expense=Decimal(approved),
            rejected_expense=Decimal(rejected),
        )
