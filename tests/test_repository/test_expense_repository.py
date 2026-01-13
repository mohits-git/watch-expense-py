from decimal import Decimal
from unittest.mock import patch, ANY
import pytest
from botocore.exceptions import ClientError
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.models.expense import Expense, ExpensesFilterOptions, RequestStatus
from app.repository.expense_repository import ExpenseRepository


@pytest.fixture
def expense_repository(mock_ddb_table, table_name):
    return ExpenseRepository(mock_ddb_table, table_name)


@pytest.fixture
def sample_expense():
    return Expense.model_validate({
        "id": "expense-123",
        "user_id": "user-456",
        "purpose": "Business travel",
        "description": "Travel to client site",
        "amount": Decimal("5000.00"),
        "status": RequestStatus.Pending,
        "is_reconciled": False,
        "bills": [
            {
                "id": "bill-123",
                "amount": Decimal("5000.00"),
                "description": "Hotel bill",
                "attachment_url": "https://example.com/bill1.pdf",
            }
        ],
        "created_at": 1704067200000,
        "updated_at": 1704067200000,
    })


@pytest.fixture
def sample_expense_item():
    return {
        "PK": "EXPENSE#expense-123",
        "SK": "DETAILS",
        "ExpenseID": "expense-123",
        "UserID": "user-456",
        "Purpose": "Business travel",
        "Description": "Travel to client site",
        "Amount": Decimal("5000.00"),
        "Status": "PENDING",
        "IsReconciled": False,
        "Bills": [
            {
                "BillID": "bill-123",
                "Amount": Decimal("5000.00"),
                "Description": "Hotel bill",
                "AttachmentURL": "https://example.com/bill1.pdf",
            }
        ],
        "CreatedAt": 1704067200000,
        "UpdatedAt": 1704067200000,
    }


class TestExpenseRepositorySave:
    @pytest.mark.asyncio
    @patch("uuid.uuid4")
    @patch("time.time_ns")
    async def test_save_success(
        self,
        mock_time_ns,
        mock_uuid,
        expense_repository,
        mock_ddb_table,
    ):
        mock_uuid.return_value.hex = "new-expense-id"
        mock_time_ns.return_value = 1704067200000000000
        mock_ddb_table.meta.client.transact_write_items.return_value = None

        expense = Expense.model_validate({
            "user_id": "user-123",
            "purpose": "Travel",
            "description": "Business trip",
            "amount": Decimal("3000.00"),
            "status": RequestStatus.Pending,
            "is_reconciled": False,
            "bills": [],
        })

        await expense_repository.save(expense)

        mock_ddb_table.meta.client.transact_write_items.assert_called_once()
        call_args = mock_ddb_table.meta.client.transact_write_items.call_args[1]
        assert len(call_args["TransactItems"]) == 3
        assert all("Put" in item for item in call_args["TransactItems"])

    @pytest.mark.asyncio
    @patch("app.repository.utils.is_conditional_check_failure")
    async def test_save_expense_already_exists(
        self,
        mock_is_conditional_check_failure,
        expense_repository,
        mock_ddb_table,
        sample_expense,
    ):
        error_response = {"Error": {"Code": "TransactionCanceledException"}}
        mock_ddb_table.meta.client.transact_write_items.side_effect = ClientError(
            error_response, "TransactWriteItems"
        )
        mock_is_conditional_check_failure.return_value = True

        with pytest.raises(AppException) as exc_info:
            await expense_repository.save(sample_expense)

        assert exc_info.value.err_code == AppErr.EXPENSE_ALREADY_EXISTS


class TestExpenseRepositoryGet:
    @pytest.mark.asyncio
    async def test_get_success(
        self,
        expense_repository,
        mock_ddb_table,
        sample_expense_item,
    ):
        mock_ddb_table.get_item.return_value = {"Item": sample_expense_item}

        result = await expense_repository.get("expense-123")

        assert result is not None
        assert result.id == "expense-123"
        assert result.user_id == "user-456"
        assert result.purpose == "Business travel"
        assert result.amount == Decimal("5000.00")
        assert result.status == RequestStatus.Pending
        assert result.is_reconciled is False
        assert len(result.bills) == 1
        assert result.bills[0].amount == Decimal("5000.00")
        mock_ddb_table.get_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_not_found(
        self,
        expense_repository,
        mock_ddb_table,
    ):
        mock_ddb_table.get_item.return_value = {}

        result = await expense_repository.get("non-existent-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_client_error(
        self,
        expense_repository,
        mock_ddb_table,
    ):
        error_response = {"Error": {"Code": "ResourceNotFoundException"}}
        mock_ddb_table.get_item.side_effect = ClientError(error_response, "GetItem")

        with pytest.raises(AppException) as exc_info:
            await expense_repository.get("expense-123")

        assert exc_info.value.err_code == AppErr.INTERNAL


class TestExpenseRepositoryUpdate:
    @pytest.mark.asyncio
    @patch("time.time_ns")
    async def test_update_success(
        self,
        mock_time_ns,
        expense_repository,
        mock_ddb_table,
        sample_expense,
        sample_expense_item,
    ):
        mock_time_ns.return_value = 1704070800000000000
        mock_ddb_table.get_item.return_value = {"Item": sample_expense_item}
        mock_ddb_table.meta.client.transact_write_items.return_value = None

        sample_expense.purpose = "Updated purpose"
        sample_expense.status = RequestStatus.Approved

        await expense_repository.update(sample_expense)

        mock_ddb_table.get_item.assert_called_once()
        mock_ddb_table.meta.client.transact_write_items.assert_called_once()
        call_args = mock_ddb_table.meta.client.transact_write_items.call_args[1]
        assert len(call_args["TransactItems"]) == 3
        assert all("Update" in item for item in call_args["TransactItems"])

    @pytest.mark.asyncio
    async def test_update_not_found(
        self,
        expense_repository,
        mock_ddb_table,
        sample_expense,
    ):
        mock_ddb_table.get_item.return_value = {}

        with pytest.raises(AppException) as exc_info:
            await expense_repository.update(sample_expense)

        assert exc_info.value.err_code == AppErr.NOT_FOUND


class TestExpenseRepositoryGetAll:
    @pytest.mark.asyncio
    @patch("app.repository.utils.query_items")
    @patch("app.repository.utils.offset_query")
    async def test_get_all_no_filter(
        self,
        mock_offset_query,
        mock_query_items,
        expense_repository,
        mock_ddb_table,
    ):
        mock_ddb_table.query.return_value = {"Count": 3}
        mock_offset_query.return_value = {
            "KeyConditionExpression": ANY,
            "Select": "COUNT",
        }
        mock_query_items.return_value = [
            {
                "ExpenseID": "expense-1",
                "UserID": "user-1",
                "Purpose": "Purpose 1",
                "Description": "Desc 1",
                "Amount": Decimal("1000.00"),
                "Status": "PENDING",
                "IsReconciled": False,
                "Bills": [],
                "CreatedAt": 1704067200000,
                "UpdatedAt": 1704067200000,
            },
            {
                "ExpenseID": "expense-2",
                "UserID": "user-1",
                "Purpose": "Purpose 2",
                "Description": "Desc 2",
                "Amount": Decimal("2000.00"),
                "Status": "APPROVED",
                "IsReconciled": True,
                "Bills": [],
                "CreatedAt": 1704067300000,
                "UpdatedAt": 1704067300000,
            },
        ]

        filter_options = ExpensesFilterOptions(
            user_id="user-1",
            page=1,
            limit=10,
        )

        expenses, total = await expense_repository.get_all(filter_options)

        assert total == 3
        assert len(expenses) == 2
        assert expenses[0].id == "expense-1"
        assert expenses[1].id == "expense-2"
        mock_ddb_table.query.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.repository.utils.query_items")
    @patch("app.repository.utils.offset_query")
    async def test_get_all_with_status_filter(
        self,
        mock_offset_query,
        mock_query_items,
        expense_repository,
        mock_ddb_table,
    ):
        mock_ddb_table.query.return_value = {"Count": 1}
        mock_offset_query.return_value = {
            "KeyConditionExpression": ANY,
            "FilterExpression": ANY,
        }
        mock_query_items.return_value = [
            {
                "ExpenseID": "expense-1",
                "UserID": "user-1",
                "Purpose": "Purpose 1",
                "Description": "Desc 1",
                "Amount": Decimal("1000.00"),
                "Status": "PENDING",
                "IsReconciled": False,
                "Bills": [],
                "CreatedAt": 1704067200000,
                "UpdatedAt": 1704067200000,
            },
        ]

        filter_options = ExpensesFilterOptions(
            user_id="user-1",
            page=1,
            limit=10,
            status=RequestStatus.Pending,
        )

        expenses, total = await expense_repository.get_all(filter_options)

        assert total == 1
        assert len(expenses) == 1
        assert expenses[0].status == RequestStatus.Pending

    @pytest.mark.asyncio
    @patch("app.repository.utils.offset_query")
    async def test_get_all_empty_result(
        self,
        mock_offset_query,
        expense_repository,
        mock_ddb_table,
    ):
        mock_ddb_table.query.return_value = {"Count": 0}
        mock_offset_query.return_value = None

        filter_options = ExpensesFilterOptions(
            user_id="non-existent-user",
            page=1,
            limit=10,
        )

        expenses, total = await expense_repository.get_all(filter_options)

        assert total == 0
        assert len(expenses) == 0


class TestExpenseRepositoryGetSum:
    @pytest.mark.asyncio
    @patch("app.repository.utils.query_items")
    async def test_get_sum_success(
        self,
        mock_query_items,
        expense_repository,
    ):
        mock_query_items.return_value = [
            {"Amount": Decimal("1000.00")},
            {"Amount": Decimal("2000.00")},
            {"Amount": Decimal("3000.00")},
        ]

        total = await expense_repository.get_sum("user-123")

        assert total == 6000.00

    @pytest.mark.asyncio
    @patch("app.repository.utils.query_items")
    async def test_get_sum_with_status(
        self,
        mock_query_items,
        expense_repository,
    ):
        mock_query_items.return_value = [
            {"Amount": Decimal("1000.00")},
            {"Amount": Decimal("2000.00")},
        ]

        total = await expense_repository.get_sum("user-123", RequestStatus.Pending)

        assert total == 3000.00

    @pytest.mark.asyncio
    @patch("app.repository.utils.query_items")
    async def test_get_sum_empty(
        self,
        mock_query_items,
        expense_repository,
    ):
        mock_query_items.return_value = []

        total = await expense_repository.get_sum("user-123")

        assert total == 0.0
