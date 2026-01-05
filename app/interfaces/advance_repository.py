from typing import Protocol

from app.models.advance import Advance, AdvancesFilterOptions
from app.models.expense import RequestStatus


class AdvanceRepository(Protocol):
    async def save(self, advance: Advance) -> None: ...
    async def get(self, advance_id: str) -> Advance | None: ...
    async def update(self, advance: Advance) -> None: ...

    async def get_all(self,
                      filterOptions: AdvancesFilterOptions,
                      ) -> tuple[list[Advance], int]: ...

    async def get_sum_by_status(self,
                                user_id: str = "",
                                status: RequestStatus | None = None) -> float: ...

    async def get_reconciled_advance_sum(self, user_id: str) -> float: ...
