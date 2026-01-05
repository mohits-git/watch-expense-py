import pytest
import time
from decimal import Decimal
from app.models.expense import RequestStatus
from app.models.advance import Advance, AdvancesFilterOptions
from app.repository import create_ddb_resource
from app.repository.advance_repository import AdvanceRepository


@pytest.fixture
def advance_repository() -> AdvanceRepository:
    ddb_resource = create_ddb_resource()
    return AdvanceRepository(ddb_resource, "watch-expense-table")


class TestAdvanceRepository:
    def test_get_all(self, advance_repository):
        # filterOptions = AdvancesFilterOptions(
        #     user_id="",
        #     status=RequestStatus.Approved,
        #     page=0,
        #     limit=5,
        # )
        # print(advance_repository.get_all(filterOptions))
        # TODO: tests
        pass

    def test_get(self, advance_repository):
        # print(advance_repository.get("a97a4962-dcb9-43a4-aed4-2f5c23a352c0"))
        pass

    def test_save(self, advance_repository):
        # advance = Advance(
        #     id="a97a4962-dcb9-43a4-aed4-2f5c23a352c0",
        #     user_id="4e3e8d1a-99f1-4b50-997d-4dac70832fb6",
        #     amount=Decimal("101"),
        #     description="Testing Advance Request",
        #     purpose="Testing Advance",
        #     status=RequestStatus.Pending,
        #     reconciled_expense_id="",
        # )
        # advance_repository.save(advance)
        pass

    def test_update(self, advance_repository):
        # advance = Advance(
        #     id="a97a4962-dcb9-43a4-aed4-2f5c23a352c0",
        #     user_id="4e3e8d1a-99f1-4b50-997d-4dac70832fb6",
        #     amount=Decimal("102"),
        #     description="Testing Advance Request",
        #     purpose="Testing Advance",
        #     status=RequestStatus.Approved,
        #     reconciled_expense_id="a97a4962-dcb9-43a4-aed4-2f5c23a352c0",
        #     approved_at=int(time.time_ns()//1e6),
        #     approved_by="589c725c-f47b-442c-bd41-b9687ae8d645",
        #     reviewed_at=int(time.time_ns()//1e6),
        #     reviewed_by="589c725c-f47b-442c-bd41-b9687ae8d645",
        # )
        # advance_repository.update(advance)
        # print(advance_repository.get(advance.id))
        pass

    def test_get_sum_by_status(self, advance_repository):
        # advance_sum_all = advance_repository.get_sum_by_status()
        # advance_sum_pending = advance_repository.get_sum_by_status(status=RequestStatus.Approved)
        # advance_sum_user = advance_repository.get_sum_by_status(user_id="4e3e8d1a-99f1-4b50-997d-4dac70832fb6")
        # print('-------------')
        # print("ALL: ", advance_sum_all)
        # print("Pending: ", advance_sum_pending)
        # print("User: ", advance_sum_user)
        # print('-------------')
        pass

    def test_get_reconciled_advanced_sum(self, advance_repository):
        # user_id = "4e3e8d1a-99f1-4b50-997d-4dac70832fb6"
        # print(advance_repository.get_reconciled_advance_sum(user_id))
        pass
