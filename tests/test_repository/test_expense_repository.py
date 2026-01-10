from decimal import Decimal
from uuid import uuid4
import pytest
import pytest_asyncio
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.models.expense import Bill, Expense, ExpensesFilterOptions, RequestStatus
from app.repository.expense_repository import ExpenseRepository


class TestExpenseRepository:
    @pytest_asyncio.fixture(scope="class")
    async def expense_repository(self, ddb_table, table_name):
        return ExpenseRepository(ddb_table, table_name)

    @pytest_asyncio.fixture(scope="class")
    async def user_id(self) -> str:
        return uuid4().hex

    @pytest_asyncio.fixture(scope="class")
    async def expense_uuid(self) -> str:
        return uuid4().hex

    @pytest_asyncio.fixture(scope="class")
    async def expense(self, expense_uuid, user_id):
        return Expense.model_validate({
            "id": expense_uuid,
            "user_id": user_id,
            "purpose": "test purpose",
            "description": "test description",
            "amount": Decimal("150.75"),
            "status": RequestStatus.Pending,
            "is_reconciled": False,
            "bills": [
                {
                    "id": uuid4().hex,
                    "amount": Decimal("150.75"),
                    "description": "bill 1",
                    "attachment_url": "https://example.com/bill1.pdf",
                }
            ],
        })

    @pytest.mark.asyncio
    async def test_save(self, expense_repository, expense):
        await expense_repository.save(expense)

    @pytest.mark.asyncio
    async def test_save_expense_already_exist(self, expense_repository, expense):
        with pytest.raises(AppException) as app_exc:
            await expense_repository.save(expense)
        assert app_exc.value.err_code == AppErr.EXPENSE_ALREADY_EXISTS

    @pytest.mark.asyncio
    async def test_get(self, expense_repository, expense):
        result = await expense_repository.get(expense.id)
        assert result is not None
        assert result.id == expense.id
        assert result.user_id == expense.user_id
        assert result.purpose == expense.purpose
        assert result.description == expense.description
        assert result.amount == expense.amount
        assert result.status == expense.status
        assert result.is_reconciled == expense.is_reconciled
        assert len(result.bills) == 1
        assert result.bills[0].amount == expense.bills[0].amount

    @pytest.mark.asyncio
    async def test_get_non_existent(self, expense_repository):
        result = await expense_repository.get("non-existent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_update(self, expense_repository, expense):
        expense.purpose = "updated purpose"
        expense.description = "updated description"
        expense.amount = Decimal("300.00")
        expense.status = RequestStatus.Approved

        await expense_repository.update(expense)

        result = await expense_repository.get(expense.id)
        assert result is not None
        assert result.purpose == "updated purpose"
        assert result.description == "updated description"
        assert result.amount == Decimal("300.00")
        assert result.status == RequestStatus.Approved

    @pytest.mark.asyncio
    async def test_update_non_existent(self, expense_repository, user_id):
        non_existent_expense = Expense.model_validate({
            "id": "non-existent-id",
            "user_id": user_id,
            "purpose": "test",
            "description": "test",
            "amount": Decimal("100"),
            "status": RequestStatus.Pending,
            "is_reconciled": False,
        })
        with pytest.raises(AppException) as app_exc:
            await expense_repository.update(non_existent_expense)
        assert app_exc.value.err_code == AppErr.NOT_FOUND


class TestExpenseRepositoryGetAll:
    """Test class for get_all with multiple expenses"""

    @pytest_asyncio.fixture(scope="class")
    async def expense_repository(self, ddb_table, table_name):
        return ExpenseRepository(ddb_table, table_name)

    @pytest_asyncio.fixture(scope="class")
    async def user_id(self) -> str:
        return uuid4().hex

    @pytest_asyncio.fixture(scope="class")
    async def setup_expenses(self, expense_repository, user_id):
        """Create multiple expenses for testing get_all and aggregation methods"""
        expenses = [
            Expense.model_validate({
                "id": uuid4().hex,
                "user_id": user_id,
                "purpose": f"purpose {i}",
                "description": f"description {i}",
                "amount": Decimal(f"{100 * (i + 1)}"),
                "status": RequestStatus.Pending if i % 3 == 0 else (
                    RequestStatus.Approved if i % 3 == 1 else RequestStatus.Rejected
                ),
                "is_reconciled": i % 2 == 0,
                "bills": [],
            })
            for i in range(5)
        ]

        for expense in expenses:
            await expense_repository.save(expense)

        return expenses

    @pytest.mark.asyncio
    async def test_get_all_no_filter(self, expense_repository, user_id, setup_expenses):
        filter_options = ExpensesFilterOptions(user_id=user_id, page=1, limit=10)
        expenses, total = await expense_repository.get_all(filter_options)

        assert total == 5
        assert len(expenses) == 5

    @pytest.mark.asyncio
    async def test_get_all_with_pagination(self, expense_repository, user_id, setup_expenses):
        filter_options = ExpensesFilterOptions(user_id=user_id, page=1, limit=2)
        expenses, total = await expense_repository.get_all(filter_options)

        assert total == 5
        assert len(expenses) == 2

    @pytest.mark.asyncio
    async def test_get_all_with_status_filter(self, expense_repository, user_id, setup_expenses):
        filter_options = ExpensesFilterOptions(
            user_id=user_id,
            page=1,
            limit=10,
            status=RequestStatus.Pending
        )
        expenses, total = await expense_repository.get_all(filter_options)

        # Indices 0, 3 have Pending status (i % 3 == 0)
        assert total == 2
        for expense in expenses:
            assert expense.status == RequestStatus.Pending

    @pytest.mark.asyncio
    async def test_get_all_empty_result(self, expense_repository):
        non_existent_user_id = uuid4().hex
        filter_options = ExpensesFilterOptions(
            user_id=non_existent_user_id,
            page=1,
            limit=10
        )
        expenses, total = await expense_repository.get_all(filter_options)

        assert total == 0
        assert len(expenses) == 0

    @pytest.mark.asyncio
    async def test_get_sum(self, expense_repository, user_id, setup_expenses):
        # Total sum: 100 + 200 + 300 + 400 + 500 = 1500
        total_sum = await expense_repository.get_sum(user_id)
        assert total_sum == 1500.0

    @pytest.mark.asyncio
    async def test_get_sum_with_status(self, expense_repository, user_id, setup_expenses):
        # Pending expenses: indices 0, 3 -> amounts 100 + 400 = 500
        pending_sum = await expense_repository.get_sum(user_id, RequestStatus.Pending)
        assert pending_sum == 500.0

    @pytest.mark.asyncio
    async def test_get_sum_empty(self, expense_repository):
        non_existent_user_id = uuid4().hex
        total_sum = await expense_repository.get_sum(non_existent_user_id)
        assert total_sum == 0.0
