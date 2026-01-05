import pytest
import time
from decimal import Decimal
from app.models.expense import Bill, Expense, ExpensesFilterOptions, RequestStatus
from app.repository import create_ddb_resource
from app.repository.expense_repository import ExpenseRepository


@pytest.fixture
def expense_repository() -> ExpenseRepository:
    ddb_resource = create_ddb_resource()
    return ExpenseRepository(ddb_resource, "watch-expense-table")


class TestExpenseRepository:
    def test_get_all(self, expense_repository):
        # filterOptions = ExpensesFilterOptions(
        #     user_id="",
        #     status=RequestStatus.Pending,
        #     page=0,
        #     limit=5,
        # )
        # print(expense_repository.get_all(filterOptions))
        # TODO: tests
        pass

    def test_get(self, expense_repository):
        # print(expense_repository.get("a97a4962-dcb9-43a4-aed4-2f5c23a352c0"))
        pass

    def test_save(self, expense_repository):
        # expense = Expense(
        #     id="a97a4962-dcb9-43a4-aed4-2f5c23a352c0",
        #     user_id="4e3e8d1a-99f1-4b50-997d-4dac70832fb6",
        #     amount=Decimal("101"),
        #     description="Testing Expense Request",
        #     purpose="Testing Expense",
        #     status=RequestStatus.Pending,
        #     is_reconciled=False,
        #     bills=[Bill(
        #         id="4dbc7acf-dfbb-4eec-afea-864a5e55c4ee",
        #         amount=Decimal("101"),
        #         description="reciept test",
        #         attachment_url="https://watch-expense-bucket.s3.amazonaws.com/4e8d6de9-b585-44a2-acb9-54fabac3ed8f_Screenshot 2025-11-10 144458.png",
        #     )],
        # )
        # expense_repository.save(expense)
        pass

    def test_update(self, expense_repository):
        # expense = Expense(
        #     id="a97a4962-dcb9-43a4-aed4-2f5c23a352c0",
        #     user_id="4e3e8d1a-99f1-4b50-997d-4dac70832fb6",
        #     amount=Decimal("102"),
        #     description="Testing Expense Request",
        #     purpose="Testing Expense",
        #     status=RequestStatus.Approved,
        #     is_reconciled=False,
        #     approved_at=int(time.time_ns()//1e6),
        #     approved_by="589c725c-f47b-442c-bd41-b9687ae8d645",
        #     reviewed_at=int(time.time_ns()//1e6),
        #     reviewed_by="589c725c-f47b-442c-bd41-b9687ae8d645",
        #     bills=[Bill(
        #         id="4dbc7acf-dfbb-4eec-afea-864a5e55c4ee",
        #         amount=Decimal("102"),
        #         description="reciept test2",
        #         attachment_url="https://watch-expense-bucket.s3.amazonaws.com/4e8d6de9-b585-44a2-acb9-54fabac3ed8f_Screenshot 2025-11-10 144458.png",
        #     )],
        # )
        # expense_repository.update(expense)
        # print(expense_repository.get(expense.id))
        pass

    def test_get_expense_status(self, expense_repository):
        # expense_sum_all = expense_repository.get_expense_sum()
        # expense_sum_pending = expense_repository.get_expense_sum(status=RequestStatus.Pending)
        # expense_sum_user = expense_repository.get_expense_sum(user_id="4e3e8d1a-99f1-4b50-997d-4dac70832fb6")
        # print('-------------')
        # print("ALL: ", expense_sum_all)
        # print("Pending: ", expense_sum_pending)
        # print("User: ", expense_sum_user)
        # print('-------------')
        pass
