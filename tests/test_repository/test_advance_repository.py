from decimal import Decimal
from unittest.mock import patch, ANY
import pytest
from botocore.exceptions import ClientError
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.models.advance import Advance, AdvancesFilterOptions, RequestStatus
from app.repository.advance_repository import AdvanceRepository


@pytest.fixture
def advance_repository(mock_ddb_table, table_name):
    return AdvanceRepository(mock_ddb_table, table_name)


@pytest.fixture
def sample_advance():
    return Advance.model_validate({
        "id": "advance-123",
        "user_id": "user-456",
        "purpose": "Business travel",
        "description": "Travel to client site",
        "amount": Decimal("5000.00"),
        "status": RequestStatus.Pending,
        "reconciled_expense_id": None,
        "created_at": 1704067200000,
        "updated_at": 1704067200000,
    })


@pytest.fixture
def sample_advance_item():
    return {
        "PK": "ADVANCE#advance-123",
        "SK": "DETAILS",
        "AdvanceID": "advance-123",
        "UserID": "user-456",
        "Purpose": "Business travel",
        "Description": "Travel to client site",
        "Amount": Decimal("5000.00"),
        "Status": "PENDING",
        "ReconciledExpenseID": None,
        "CreatedAt": 1704067200000,
        "UpdatedAt": 1704067200000,
    }


class TestAdvanceRepositorySave:
    @pytest.mark.asyncio
    @patch("uuid.uuid4")
    @patch("time.time_ns")
    async def test_save_success(
        self,
        mock_time_ns,
        mock_uuid,
        advance_repository,
        mock_ddb_table,
    ):
        mock_uuid.return_value.hex = "new-advance-id"
        mock_time_ns.return_value = 1704067200000000000
        mock_ddb_table.meta.client.transact_write_items.return_value = None

        advance = Advance.model_validate({
            "user_id": "user-123",
            "purpose": "Travel",
            "description": "Business trip",
            "amount": Decimal("3000.00"),
            "status": RequestStatus.Pending,
        })

        await advance_repository.save(advance)

        mock_ddb_table.meta.client.transact_write_items.assert_called_once()
        call_args = mock_ddb_table.meta.client.transact_write_items.call_args[1]
        assert len(call_args["TransactItems"]) == 3
        assert all("Put" in item for item in call_args["TransactItems"])

    @pytest.mark.asyncio
    @patch("app.repository.utils.is_conditional_check_failure")
    async def test_save_advance_already_exists(
        self,
        mock_is_conditional_check_failure,
        advance_repository,
        mock_ddb_table,
        sample_advance,
    ):
        error_response = {"Error": {"Code": "TransactionCanceledException"}}
        mock_ddb_table.meta.client.transact_write_items.side_effect = ClientError(
            error_response, "TransactWriteItems"
        )
        mock_is_conditional_check_failure.return_value = True

        with pytest.raises(AppException) as exc_info:
            await advance_repository.save(sample_advance)

        assert exc_info.value.err_code == AppErr.ADVANCE_ALREADY_EXISTS


class TestAdvanceRepositoryGet:
    @pytest.mark.asyncio
    async def test_get_success(
        self,
        advance_repository,
        mock_ddb_table,
        sample_advance_item,
    ):
        mock_ddb_table.get_item.return_value = {"Item": sample_advance_item}

        result = await advance_repository.get("advance-123")

        assert result is not None
        assert result.id == "advance-123"
        assert result.user_id == "user-456"
        assert result.purpose == "Business travel"
        assert result.amount == Decimal("5000.00")
        assert result.status == RequestStatus.Pending
        mock_ddb_table.get_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_not_found(
        self,
        advance_repository,
        mock_ddb_table,
    ):
        mock_ddb_table.get_item.return_value = {}

        result = await advance_repository.get("non-existent-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_client_error(
        self,
        advance_repository,
        mock_ddb_table,
    ):
        error_response = {"Error": {"Code": "ResourceNotFoundException"}}
        mock_ddb_table.get_item.side_effect = ClientError(error_response, "GetItem")

        with pytest.raises(AppException) as exc_info:
            await advance_repository.get("advance-123")

        assert exc_info.value.err_code == AppErr.INTERNAL


class TestAdvanceRepositoryUpdate:
    @pytest.mark.asyncio
    @patch("time.time_ns")
    async def test_update_success(
        self,
        mock_time_ns,
        advance_repository,
        mock_ddb_table,
        sample_advance,
        sample_advance_item,
    ):
        mock_time_ns.return_value = 1704070800000000000
        mock_ddb_table.get_item.return_value = {"Item": sample_advance_item}
        mock_ddb_table.meta.client.transact_write_items.return_value = None

        sample_advance.purpose = "Updated purpose"
        sample_advance.status = RequestStatus.Approved

        await advance_repository.update(sample_advance)

        mock_ddb_table.get_item.assert_called_once()
        mock_ddb_table.meta.client.transact_write_items.assert_called_once()
        call_args = mock_ddb_table.meta.client.transact_write_items.call_args[1]
        assert len(call_args["TransactItems"]) == 3
        assert all("Update" in item for item in call_args["TransactItems"])

    @pytest.mark.asyncio
    async def test_update_not_found(
        self,
        advance_repository,
        mock_ddb_table,
        sample_advance,
    ):
        mock_ddb_table.get_item.return_value = {}

        with pytest.raises(AppException) as exc_info:
            await advance_repository.update(sample_advance)

        assert exc_info.value.err_code == AppErr.NOT_FOUND


class TestAdvanceRepositoryGetAll:
    @pytest.mark.asyncio
    @patch("app.repository.utils.query_items")
    @patch("app.repository.utils.offset_query")
    async def test_get_all_no_filter(
        self,
        mock_offset_query,
        mock_query_items,
        advance_repository,
        mock_ddb_table,
    ):
        mock_ddb_table.query.return_value = {"Count": 3}
        mock_offset_query.return_value = {
            "KeyConditionExpression": ANY,
            "Select": "COUNT",
        }
        mock_query_items.return_value = [
            {
                "AdvanceID": "advance-1",
                "UserID": "user-1",
                "Purpose": "Purpose 1",
                "Description": "Desc 1",
                "Amount": Decimal("1000.00"),
                "Status": "PENDING",
                "CreatedAt": 1704067200000,
                "UpdatedAt": 1704067200000,
            },
            {
                "AdvanceID": "advance-2",
                "UserID": "user-1",
                "Purpose": "Purpose 2",
                "Description": "Desc 2",
                "Amount": Decimal("2000.00"),
                "Status": "APPROVED",
                "CreatedAt": 1704067300000,
                "UpdatedAt": 1704067300000,
            },
        ]

        filter_options = AdvancesFilterOptions(
            user_id="user-1",
            page=1,
            limit=10,
        )

        advances, total = await advance_repository.get_all(filter_options)

        assert total == 3
        assert len(advances) == 2
        assert advances[0].id == "advance-1"
        assert advances[1].id == "advance-2"
        mock_ddb_table.query.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.repository.utils.query_items")
    @patch("app.repository.utils.offset_query")
    async def test_get_all_with_status_filter(
        self,
        mock_offset_query,
        mock_query_items,
        advance_repository,
        mock_ddb_table,
    ):
        mock_ddb_table.query.return_value = {"Count": 1}
        mock_offset_query.return_value = {
            "KeyConditionExpression": ANY,
            "FilterExpression": ANY,
        }
        mock_query_items.return_value = [
            {
                "AdvanceID": "advance-1",
                "UserID": "user-1",
                "Purpose": "Purpose 1",
                "Description": "Desc 1",
                "Amount": Decimal("1000.00"),
                "Status": "PENDING",
                "CreatedAt": 1704067200000,
                "UpdatedAt": 1704067200000,
            },
        ]

        filter_options = AdvancesFilterOptions(
            user_id="user-1",
            page=1,
            limit=10,
            status=RequestStatus.Pending,
        )

        advances, total = await advance_repository.get_all(filter_options)

        assert total == 1
        assert len(advances) == 1
        assert advances[0].status == RequestStatus.Pending

    @pytest.mark.asyncio
    @patch("app.repository.utils.offset_query")
    async def test_get_all_empty_result(
        self,
        mock_offset_query,
        advance_repository,
        mock_ddb_table,
    ):
        mock_ddb_table.query.return_value = {"Count": 0}
        mock_offset_query.return_value = None

        filter_options = AdvancesFilterOptions(
            user_id="non-existent-user",
            page=1,
            limit=10,
        )

        advances, total = await advance_repository.get_all(filter_options)

        assert total == 0
        assert len(advances) == 0


class TestAdvanceRepositoryGetSum:
    @pytest.mark.asyncio
    @patch("app.repository.utils.query_items")
    async def test_get_sum_success(
        self,
        mock_query_items,
        advance_repository,
    ):
        mock_query_items.return_value = [
            {"Amount": Decimal("1000.00")},
            {"Amount": Decimal("2000.00")},
            {"Amount": Decimal("3000.00")},
        ]

        total = await advance_repository.get_sum("user-123")

        assert total == 6000.00

    @pytest.mark.asyncio
    @patch("app.repository.utils.query_items")
    async def test_get_sum_with_status(
        self,
        mock_query_items,
        advance_repository,
    ):
        mock_query_items.return_value = [
            {"Amount": Decimal("1000.00")},
            {"Amount": Decimal("2000.00")},
        ]

        total = await advance_repository.get_sum("user-123", RequestStatus.Pending)

        assert total == 3000.00

    @pytest.mark.asyncio
    @patch("app.repository.utils.query_items")
    async def test_get_sum_empty(
        self,
        mock_query_items,
        advance_repository,
    ):
        mock_query_items.return_value = []

        total = await advance_repository.get_sum("user-123")

        assert total == 0.0


class TestAdvanceRepositoryGetReconciledSum:
    @pytest.mark.asyncio
    @patch("app.repository.utils.query_items")
    async def test_get_reconciled_sum_success(
        self,
        mock_query_items,
        advance_repository,
    ):
        mock_query_items.return_value = [
            {"Amount": Decimal("1500.00")},
            {"Amount": Decimal("2500.00")},
        ]

        total = await advance_repository.get_reconciled_sum("user-123")

        assert total == 4000.00

    @pytest.mark.asyncio
    @patch("app.repository.utils.query_items")
    async def test_get_reconciled_sum_empty(
        self,
        mock_query_items,
        advance_repository,
    ):
        mock_query_items.return_value = []

        total = await advance_repository.get_reconciled_sum("user-123")

        assert total == 0.0
