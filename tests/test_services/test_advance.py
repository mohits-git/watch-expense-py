from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
import pytest
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.models.advance import Advance, AdvancesFilterOptions
from app.models.expense import RequestStatus
from app.models.user import UserClaims, UserRole
from app.services.advance import AdvanceService


class TestAdvanceService:
    @pytest.fixture
    def mock_advance_repo(self):
        repo = MagicMock()
        repo.get = AsyncMock()
        repo.save = AsyncMock()
        repo.update = AsyncMock()
        repo.get_all = AsyncMock()
        repo.get_sum = AsyncMock()
        repo.get_reconciled_sum = AsyncMock()
        return repo

    @pytest.fixture
    def advance_service(self, mock_advance_repo):
        return AdvanceService(mock_advance_repo)

    @pytest.fixture
    def employee_user(self):
        return UserClaims(
            id=uuid4().hex,
            name="Test Employee",
            email="employee@example.com",
            role=UserRole.Employee
        )

    @pytest.fixture
    def admin_user(self):
        return UserClaims(
            id=uuid4().hex,
            name="Test Admin",
            email="admin@example.com",
            role=UserRole.Admin
        )

    @pytest.fixture
    def sample_advance(self, employee_user):
        return Advance.model_validate({
            "id": uuid4().hex,
            "user_id": employee_user.user_id,
            "purpose": "Business trip",
            "description": "Travel advance",
            "amount": Decimal("500.00"),
            "status": RequestStatus.Pending,
        })

    @pytest.mark.asyncio
    async def test_get_advance_by_id_success_own_advance(self, advance_service, employee_user, sample_advance, mock_advance_repo):
        mock_advance_repo.get.return_value = sample_advance

        result = await advance_service.get_advance_by_id(employee_user, sample_advance.id)

        assert result == sample_advance
        mock_advance_repo.get.assert_called_once_with(sample_advance.id)

    @pytest.mark.asyncio
    async def test_get_advance_by_id_success_admin(self, advance_service, admin_user, sample_advance, mock_advance_repo):
        mock_advance_repo.get.return_value = sample_advance

        result = await advance_service.get_advance_by_id(admin_user, sample_advance.id)

        assert result == sample_advance

    @pytest.mark.asyncio
    async def test_get_advance_by_id_forbidden(self, advance_service, employee_user, sample_advance, mock_advance_repo):
        sample_advance.user_id = "different-user-id"
        mock_advance_repo.get.return_value = sample_advance

        with pytest.raises(AppException) as exc:
            await advance_service.get_advance_by_id(employee_user, sample_advance.id)

        assert exc.value.err_code == AppErr.FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_advance_by_id_not_found(self, advance_service, employee_user, mock_advance_repo):
        mock_advance_repo.get.return_value = None

        with pytest.raises(AppException) as exc:
            await advance_service.get_advance_by_id(employee_user, "non-existent-id")

        assert exc.value.err_code == AppErr.NOT_FOUND

    @pytest.mark.asyncio
    async def test_create_advance_success(self, advance_service, employee_user, mock_advance_repo):
        advance = Advance.model_validate({
            "purpose": "Conference",
            "description": "Tech conference",
            "amount": Decimal("1000.00"),
            "status": RequestStatus.Pending,
        })

        result = await advance_service.create_advance(employee_user, advance)

        assert result is not None
        assert len(result) > 0
        assert advance.user_id == employee_user.user_id
        mock_advance_repo.save.assert_called_once_with(advance)

    @pytest.mark.asyncio
    async def test_update_advance_success_own_advance(self, advance_service, employee_user, sample_advance, mock_advance_repo):
        mock_advance_repo.get.return_value = sample_advance

        await advance_service.update_advance(employee_user, sample_advance)

        mock_advance_repo.update.assert_called_once_with(sample_advance)

    @pytest.mark.asyncio
    async def test_update_advance_success_admin(self, advance_service, admin_user, sample_advance, mock_advance_repo):
        mock_advance_repo.get.return_value = sample_advance

        await advance_service.update_advance(admin_user, sample_advance)

        mock_advance_repo.update.assert_called_once_with(sample_advance)

    @pytest.mark.asyncio
    async def test_update_advance_not_found(self, advance_service, employee_user, sample_advance, mock_advance_repo):
        mock_advance_repo.get.return_value = None

        with pytest.raises(AppException) as exc:
            await advance_service.update_advance(employee_user, sample_advance)

        assert exc.value.err_code == AppErr.NOT_FOUND

    @pytest.mark.asyncio
    async def test_update_advance_forbidden(self, advance_service, employee_user, sample_advance, mock_advance_repo):
        sample_advance.user_id = "different-user-id"
        mock_advance_repo.get.return_value = sample_advance

        with pytest.raises(AppException) as exc:
            await advance_service.update_advance(employee_user, sample_advance)

        assert exc.value.err_code == AppErr.FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_all_advances_employee(self, advance_service, employee_user, sample_advance, mock_advance_repo):
        mock_advance_repo.get_all.return_value = ([sample_advance], 1)
        filter_options = AdvancesFilterOptions(page=1, limit=10)

        advances, total = await advance_service.get_all_advances(employee_user, filter_options)

        assert len(advances) == 1
        assert total == 1
        assert filter_options.user_id == employee_user.user_id

    @pytest.mark.asyncio
    async def test_get_all_advances_admin(self, advance_service, admin_user, sample_advance, mock_advance_repo):
        mock_advance_repo.get_all.return_value = ([sample_advance], 1)
        filter_options = AdvancesFilterOptions(page=1, limit=10)

        advances, total = await advance_service.get_all_advances(admin_user, filter_options)

        assert len(advances) == 1
        assert total == 1
        assert filter_options.user_id is None

    @pytest.mark.asyncio
    async def test_update_advance_status_approved(self, advance_service, sample_advance, mock_advance_repo):
        mock_advance_repo.get.return_value = sample_advance
        admin_id = uuid4().hex

        await advance_service.update_advance_status(admin_id, sample_advance.id, RequestStatus.Approved)

        assert sample_advance.status == RequestStatus.Approved
        assert sample_advance.approved_by == admin_id
        assert sample_advance.approved_at is not None
        mock_advance_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_advance_status_reviewed(self, advance_service, sample_advance, mock_advance_repo):
        mock_advance_repo.get.return_value = sample_advance
        reviewer_id = uuid4().hex

        await advance_service.update_advance_status(reviewer_id, sample_advance.id, RequestStatus.Reviewed)

        assert sample_advance.status == RequestStatus.Reviewed
        assert sample_advance.reviewed_by == reviewer_id
        assert sample_advance.reviewed_at is not None
        mock_advance_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_advance_status_not_found(self, advance_service, mock_advance_repo):
        mock_advance_repo.get.return_value = None

        with pytest.raises(AppException) as exc:
            await advance_service.update_advance_status(uuid4().hex, "non-existent-id", RequestStatus.Approved)

        assert exc.value.err_code == AppErr.NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_advance_summary_employee(self, advance_service, employee_user, mock_advance_repo):
        mock_advance_repo.get_sum.return_value = 1000.0
        mock_advance_repo.get_reconciled_sum.return_value = 500.0

        summary = await advance_service.get_advance_summary(employee_user)

        assert summary.approved == Decimal("1000.0")
        assert summary.reconciled == Decimal("500.0")
        assert summary.pending == Decimal("1000.0")
        assert summary.rejected == Decimal("1000.0")

    @pytest.mark.asyncio
    async def test_get_advance_summary_admin(self, advance_service, admin_user, mock_advance_repo):
        mock_advance_repo.get_sum.return_value = 5000.0
        mock_advance_repo.get_reconciled_sum.return_value = 2000.0

        summary = await advance_service.get_advance_summary(admin_user)

        assert summary.approved == Decimal("5000.0")
        assert summary.reconciled == Decimal("2000.0")
