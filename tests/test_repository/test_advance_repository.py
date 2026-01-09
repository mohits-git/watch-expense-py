from decimal import Decimal
import time
import pytest
import pytest_asyncio
from app.models.advance import Advance, AdvancesFilterOptions
from app.models.expense import RequestStatus
from app.repository import get_boto3_session
from app.repository.advance_repository import AdvanceRepository


@pytest_asyncio.fixture
async def advance_repository():
    session = get_boto3_session()
    async with session.resource("dynamodb") as ddb_resource:
        ddb_table = await ddb_resource.Table("watch-expense-table")
        yield AdvanceRepository(ddb_table, "watch-expense-table")


class TestAdvanceRepository:
    @pytest.mark.asyncio
    async def test_get_all(self, advance_repository):
        filterOptions = AdvancesFilterOptions(
            user_id="",
            status=RequestStatus.Approved,
            page=0,
            limit=5,
        )
        print(await advance_repository.get_all(filterOptions))
        # TODO: tests
        pass

    @pytest.mark.asyncio
    async def test_get(self, advance_repository):
        print(await advance_repository.get("a97a4962-dcb9-43a4-aed4-2f5c23a352c0"))
        pass

    @pytest.mark.asyncio
    async def test_save(self, advance_repository):
        advance = Advance.model_validate(
            {
                "id": "a97a4962-dcb9-43a4-aed4-2f5c23a352c0",
                "user_id": "4e3e8d1a-99f1-4b50-997d-4dac70832fb6",
                "amount": Decimal("101"),
                "description": "Testing Advance Request",
                "purpose": "Testing Advance",
                "status": RequestStatus.Pending,
                "reconciled_expense_id": "",
            }
        )
        await advance_repository.save(advance)
        pass

    @pytest.mark.asyncio
    async def test_update(self, advance_repository):
        advance = Advance.model_validate(
            {
                "id": "a97a4962-dcb9-43a4-aed4-2f5c23a352c0",
                "user_id": "4e3e8d1a-99f1-4b50-997d-4dac70832fb6",
                "amount": Decimal("102"),
                "description": "Testing Advance Request",
                "purpose": "Testing Advance",
                "status": RequestStatus.Approved,
                "reconciled_expense_id": "a97a4962-dcb9-43a4-aed4-2f5c23a352c0",
                "approved_at": int(time.time_ns() // 1e6),
                "approved_by": "589c725c-f47b-442c-bd41-b9687ae8d645",
                "reviewed_at": int(time.time_ns() // 1e6),
                "reviewed_by": "589c725c-f47b-442c-bd41-b9687ae8d645",
            }
        )
        await advance_repository.update(advance)
        print(advance_repository.get(advance.id))
        pass

    @pytest.mark.asyncio
    async def test_get_sum_by_status(self, advance_repository):
        advance_sum_all = await advance_repository.get_sum_by_status()
        advance_sum_pending = await advance_repository.get_sum_by_status(
            status=RequestStatus.Approved
        )
        advance_sum_user = await advance_repository.get_sum_by_status(
            user_id="4e3e8d1a-99f1-4b50-997d-4dac70832fb6"
        )
        print("-------------")
        print("ALL: ", advance_sum_all)
        print("Pending: ", advance_sum_pending)
        print("User: ", advance_sum_user)
        print("-------------")
        pass

    @pytest.mark.asyncio
    async def test_get_reconciled_advanced_sum(self, advance_repository):
        user_id = "4e3e8d1a-99f1-4b50-997d-4dac70832fb6"
        print(await advance_repository.get_advance_sum(user_id))
        pass
