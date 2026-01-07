from decimal import Decimal
import time
import asyncio
from uuid import uuid4
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.interfaces import AdvanceRepository
from app.models.advance import Advance, AdvanceSummary, AdvancesFilterOptions
from app.models.expense import RequestStatus


class AdvanceService:
    def __init__(self, advance_repo: AdvanceRepository):
        self.advance_repo = advance_repo

    async def get_advance_by_id(self, advance_id: str) -> Advance:
        advance = await self.advance_repo.get(advance_id)
        if not advance:
            raise AppException(
                AppErr.ADVANCE_NOT_FOUND, f"Advance with ID {advance_id} not found"
            )
        return advance

    async def create_advance(self, advance: Advance) -> str:
        advance.id = uuid4().hex
        await self.advance_repo.save(advance)
        return advance.id

    async def update_advance(self, advance: Advance) -> None:
        existing_advance = await self.advance_repo.get(advance.id)
        if not existing_advance:
            raise AppException(
                AppErr.ADVANCE_NOT_FOUND, f"Advance with ID {advance.id} not found"
            )
        await self.advance_repo.update(advance)

    async def get_all_advances(
        self, filter_options: AdvancesFilterOptions
    ) -> tuple[list[Advance], int]:
        advances, total_count = await self.advance_repo.get_all(filter_options)
        return advances, total_count

    async def update_advance_status(
        self, curr_user_id: str, advance_id: str, status: RequestStatus
    ) -> None:
        existing_advance = await self.advance_repo.get(advance_id)
        if not existing_advance:
            raise AppException(AppErr.ADVANCE_NOT_FOUND)
        existing_advance.status = status
        if status == RequestStatus.Approved:
            existing_advance.approved_by = curr_user_id
            existing_advance.approved_at = int(time.time())
        if status == RequestStatus.Reviewed:
            existing_advance.reviewed_by = curr_user_id
            existing_advance.reviewed_at = int(time.time())
        await self.advance_repo.update(existing_advance)

    async def get_advance_summary(self, user_id: str = "") -> AdvanceSummary:
        results = await asyncio.gather(
            self.advance_repo.get_sum(user_id, RequestStatus.Approved),
            self.advance_repo.get_reconciled_sum(user_id),
            self.advance_repo.get_sum(user_id, RequestStatus.Pending),
            self.advance_repo.get_sum(user_id, RequestStatus.Rejected),
        )
        approved, reconciled, pending, rejected = results

        return AdvanceSummary(
            approved=Decimal(approved),
            reconciled=Decimal(reconciled),
            pending=Decimal(pending),
            rejected=Decimal(rejected),
        )
