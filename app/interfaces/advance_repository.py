from typing import Protocol

from app.models.advance import Advance, AdvancesFilterOptions
from app.models.expense import RequestStatus


class AdvanceRepository(Protocol):
    def save(self, advance: Advance) -> None: ...
    def get(self, advance_id: str) -> Advance | None: ...
    def update(self, advance: Advance) -> None: ...

    def get_all(self,
                filterOptions: AdvancesFilterOptions,
                ) -> tuple[list[Advance], int]: ...

    def get_sum_by_status(self,
                          user_id: str = "",
                          status: RequestStatus | None = None) -> float: ...

    def get_reconciled_advance_sum(self, user_id: str) -> float: ...
