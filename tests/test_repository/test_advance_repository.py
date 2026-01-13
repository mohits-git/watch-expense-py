from decimal import Decimal
from uuid import uuid4
import pytest
import pytest_asyncio
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.models.advance import Advance, AdvancesFilterOptions
from app.models.expense import RequestStatus
from app.repository.advance_repository import AdvanceRepository


class TestAdvanceRepository:
    @pytest_asyncio.fixture(scope="class")
    async def advance_repository(self, ddb_table, table_name):
        return AdvanceRepository(ddb_table, table_name)

    @pytest_asyncio.fixture(scope="class")
    async def user_id(self) -> str:
        return uuid4().hex

    @pytest_asyncio.fixture(scope="class")
    async def advance_uuid(self) -> str:
        return uuid4().hex

    @pytest_asyncio.fixture(scope="class")
    async def advance(self, advance_uuid, user_id):
        return Advance.model_validate({
            "id": advance_uuid,
            "user_id": user_id,
            "purpose": "test purpose",
            "description": "test description",
            "amount": Decimal("100.01"),
            "status": RequestStatus.Pending,
            "reconciled_expense_id": "uuid-expense-dummy",
        })

    @pytest.mark.asyncio
    async def test_save(self, advance_repository, advance):
        await advance_repository.save(advance)

    @pytest.mark.asyncio
    async def test_save_advance_already_exist(self, advance_repository, advance):
        with pytest.raises(AppException) as app_exc:
            await advance_repository.save(advance)
        assert app_exc.value.err_code == AppErr.ADVANCE_ALREADY_EXISTS

    @pytest.mark.asyncio
    async def test_get(self, advance_repository, advance):
        result = await advance_repository.get(advance.id)
        assert result is not None
        assert result.id == advance.id
        assert result.user_id == advance.user_id
        assert result.purpose == advance.purpose
        assert result.description == advance.description
        assert result.amount == advance.amount
        assert result.status == advance.status
        assert result.reconciled_expense_id == advance.reconciled_expense_id

    @pytest.mark.asyncio
    async def test_get_non_existent(self, advance_repository):
        result = await advance_repository.get("non-existent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_update(self, advance_repository, advance):
        advance.purpose = "updated purpose"
        advance.description = "updated description"
        advance.amount = Decimal("200.50")
        advance.status = RequestStatus.Approved

        await advance_repository.update(advance)

        result = await advance_repository.get(advance.id)
        assert result is not None
        assert result.purpose == "updated purpose"
        assert result.description == "updated description"
        assert result.amount == Decimal("200.50")
        assert result.status == RequestStatus.Approved

    @pytest.mark.asyncio
    async def test_update_non_existent(self, advance_repository, user_id):
        non_existent_advance = Advance.model_validate({
            "id": "non-existent-id",
            "user_id": user_id,
            "purpose": "test",
            "description": "test",
            "amount": Decimal("100"),
            "status": RequestStatus.Pending,
        })
        with pytest.raises(AppException) as app_exc:
            await advance_repository.update(non_existent_advance)
        assert app_exc.value.err_code == AppErr.NOT_FOUND


class TestAdvanceRepositoryGetAll:
    """Test class for get_all with multiple advances"""

    @pytest_asyncio.fixture(scope="class")
    async def advance_repository(self, ddb_table, table_name):
        return AdvanceRepository(ddb_table, table_name)

    @pytest_asyncio.fixture(scope="class")
    async def user_id(self) -> str:
        return uuid4().hex

    @pytest_asyncio.fixture(scope="class")
    async def setup_advances(self, advance_repository, user_id):
        """Create multiple advances for testing get_all and aggregation methods"""
        advances = [
            Advance.model_validate({
                "id": uuid4().hex,
                "user_id": user_id,
                "purpose": f"purpose {i}",
                "description": f"description {i}",
                "amount": Decimal(f"{100 * (i + 1)}"),
                "status": RequestStatus.Pending if i % 3 == 0 else (
                    RequestStatus.Approved if i % 3 == 1 else RequestStatus.Rejected
                ),
                "reconciled_expense_id": f"expense-{i}" if i % 2 == 0 else None,
            })
            for i in range(5)
        ]

        for advance in advances:
            await advance_repository.save(advance)

        return advances

    @pytest.mark.asyncio
    async def test_get_all_no_filter(self, advance_repository, user_id, setup_advances):
        filter_options = AdvancesFilterOptions(
            user_id=user_id, page=1, limit=10)
        advances, total = await advance_repository.get_all(filter_options)

        assert total == 5
        assert len(advances) == 5

    @pytest.mark.asyncio
    async def test_get_all_with_pagination(self, advance_repository, user_id, setup_advances):
        filter_options = AdvancesFilterOptions(
            user_id=user_id, page=1, limit=2)
        advances, total = await advance_repository.get_all(filter_options)

        assert total == 5
        assert len(advances) == 2

    @pytest.mark.asyncio
    async def test_get_all_with_status_filter(self, advance_repository, user_id, setup_advances):
        filter_options = AdvancesFilterOptions(
            user_id=user_id,
            page=1,
            limit=10,
            status=RequestStatus.Pending
        )
        advances, total = await advance_repository.get_all(filter_options)

        # 0, 3
        assert total == 2
        for advance in advances:
            assert advance.status == RequestStatus.Pending

    @pytest.mark.asyncio
    async def test_get_all_empty_result(self, advance_repository):
        non_existent_user_id = uuid4().hex
        filter_options = AdvancesFilterOptions(
            user_id=non_existent_user_id,
            page=1,
            limit=10
        )
        advances, total = await advance_repository.get_all(filter_options)

        assert total == 0
        assert len(advances) == 0

    @pytest.mark.asyncio
    async def test_get_sum(self, advance_repository, user_id, setup_advances):
        total_sum = await advance_repository.get_sum(user_id)
        assert total_sum == 1500.0

    @pytest.mark.asyncio
    async def test_get_sum_with_status(self, advance_repository, user_id, setup_advances):
        # 0, 3 -> 100 + 400 = 500
        pending_sum = await advance_repository.get_sum(user_id, RequestStatus.Pending)
        assert pending_sum == 500.0

    @pytest.mark.asyncio
    async def test_get_sum_empty(self, advance_repository):
        non_existent_user_id = uuid4().hex
        total_sum = await advance_repository.get_sum(non_existent_user_id)
        assert total_sum == 0.0

    # NOTE: moto does not support complex filter expression (.size())
    # get_reconciled_sum(user_id) uses filter expression with size()
    # ignoring this test for now
    # @pytest.mark.asyncio
    # async def test_get_reconciled_sum(self, advance_repository, user_id, setup_advances):
    #     # 0, 2, 4 -> 100 + 300 + 500 = 900
    #     reconciled_sum = await advance_repository.get_reconciled_sum(user_id)
    #     assert reconciled_sum == 900.0

    @pytest.mark.asyncio
    async def test_get_reconciled_sum_empty(self, advance_repository):
        non_existent_user_id = uuid4().hex
        reconciled_sum = await advance_repository.get_reconciled_sum(non_existent_user_id)
        assert reconciled_sum == 0.0
