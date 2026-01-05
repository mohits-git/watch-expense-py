from typing import Protocol

from app.models.expense import Expense, ExpensesFilterOptions, RequestStatus


class ExpenseRepository(Protocol):
    def save(self, expense: Expense) -> None: ...
    def get(self, expense_id: str) -> Expense | None: ...
    def update(self, expense: Expense): ...

    def get_all(
        self, filterOptions: ExpensesFilterOptions
    ) -> tuple[list[Expense], int]: ...

    def get_expense_sum(self,
                        user_id: str = "",
                        status: RequestStatus | None = None) -> float: ...
