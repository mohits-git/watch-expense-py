from typing import Protocol

from app.models.expense import Expense, ExpensesFilterOptions, RequestStatus


class ExpenseRepository(Protocol):
    async def save(self, expense: Expense) -> None: ...
    async def get(self, expense_id: str) -> Expense | None: ...
    async def update(self, expense: Expense): ...

    async def get_all(
        self, filterOptions: ExpensesFilterOptions
    ) -> tuple[list[Expense], int]: ...

    async def get_sum(
        self, user_id: str = "", status: RequestStatus | None = None
    ) -> float: ...
