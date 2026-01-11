from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
import pytest
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.models.advance import Advance
from app.models.expense import Expense, ExpensesFilterOptions, RequestStatus
from app.models.user import UserClaims, UserRole
from app.services.expense import ExpenseService


class TestExpenseService:
    @pytest.fixture
    def mock_expense_repo(self):
        repo = MagicMock()
        repo.get = AsyncMock()
        repo.save = AsyncMock()
        repo.update = AsyncMock()
        repo.get_all = AsyncMock()
        repo.get_sum = AsyncMock()
        return repo

    @pytest.fixture
    def mock_advance_repo(self):
        repo = MagicMock()
        repo.get = AsyncMock()
        return repo

    @pytest.fixture
    def expense_service(self, mock_expense_repo, mock_advance_repo):
        return ExpenseService(mock_expense_repo, mock_advance_repo)

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
    def sample_expense(self, employee_user):
        return Expense.model_validate({
            "id": uuid4().hex,
            "user_id": employee_user.user_id,
            "purpose": "Office supplies",
            "description": "Notebooks and pens",
            "amount": Decimal("50.00"),
            "status": RequestStatus.Pending,
            "is_reconciled": False,
            "bills": [],
        })

    @pytest.fixture
    def sample_advance(self, employee_user):
        return Advance.model_validate({
            "id": uuid4().hex,
            "user_id": employee_user.user_id,
            "purpose": "Travel",
            "description": "Business trip",
            "amount": Decimal("500.00"),
            "status": RequestStatus.Approved,
        })

    @pytest.mark.asyncio
    async def test_get_expense_by_id_success_own_expense(self, expense_service, employee_user, sample_expense, mock_expense_repo):
        mock_expense_repo.get.return_value = sample_expense

        result = await expense_service.get_expense_by_id(employee_user, sample_expense.id)

        assert result == sample_expense
        mock_expense_repo.get.assert_called_once_with(sample_expense.id)

    @pytest.mark.asyncio
    async def test_get_expense_by_id_success_admin(self, expense_service, admin_user, sample_expense, mock_expense_repo):
        mock_expense_repo.get.return_value = sample_expense

        result = await expense_service.get_expense_by_id(admin_user, sample_expense.id)

        assert result == sample_expense

    @pytest.mark.asyncio
    async def test_get_expense_by_id_forbidden(self, expense_service, employee_user, sample_expense, mock_expense_repo):
        sample_expense.user_id = "different-user-id"
        mock_expense_repo.get.return_value = sample_expense

        with pytest.raises(AppException) as exc:
            await expense_service.get_expense_by_id(employee_user, sample_expense.id)

        assert exc.value.err_code == AppErr.FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_expense_by_id_not_found(self, expense_service, employee_user, mock_expense_repo):
        mock_expense_repo.get.return_value = None

        with pytest.raises(AppException) as exc:
            await expense_service.get_expense_by_id(employee_user, "non-existent-id")

        assert exc.value.err_code == AppErr.NOT_FOUND

    @pytest.mark.asyncio
    async def test_create_expense_success_no_advance(self, expense_service, employee_user, mock_expense_repo):
        expense = Expense.model_validate({
            "purpose": "Taxi",
            "description": "Client meeting",
            "amount": Decimal("25.00"),
            "is_reconciled": False,
            "bills": [],
        })

        result = await expense_service.create_expense(employee_user, expense)

        assert result is not None
        assert len(result) > 0
        assert expense.user_id == employee_user.user_id
        assert expense.status == RequestStatus.Pending
        assert expense.is_reconciled is False
        mock_expense_repo.save.assert_called_once_with(expense)

    @pytest.mark.asyncio
    async def test_create_expense_success_with_advance(self, expense_service, employee_user, sample_advance, mock_expense_repo, mock_advance_repo):
        mock_advance_repo.get.return_value = sample_advance
        expense = Expense.model_validate({
            "purpose": "Travel expense",
            "description": "Flight tickets",
            "amount": Decimal("300.00"),
            "advance_id": sample_advance.id,
            "is_reconciled": False,
            "bills": [],
        })

        result = await expense_service.create_expense(employee_user, expense)

        assert result is not None
        assert expense.is_reconciled is True
        mock_advance_repo.get.assert_called_once_with(sample_advance.id)
        mock_expense_repo.save.assert_called_once_with(expense, sample_advance.id)

    @pytest.mark.asyncio
    async def test_create_expense_advance_not_found(self, expense_service, employee_user, mock_advance_repo):
        mock_advance_repo.get.return_value = None
        expense = Expense.model_validate({
            "purpose": "Travel",
            "description": "Expense",
            "amount": Decimal("100.00"),
            "advance_id": "non-existent-advance-id",
            "is_reconciled": False,
            "bills": [],
        })

        with pytest.raises(AppException) as exc:
            await expense_service.create_expense(employee_user, expense)

        assert exc.value.err_code == AppErr.INVALID_EXPENSE_RECONCILE_ADVANCE

    @pytest.mark.asyncio
    async def test_create_expense_advance_permission_denied(self, expense_service, employee_user, sample_advance, mock_advance_repo):
        sample_advance.user_id = "different-user-id"
        mock_advance_repo.get.return_value = sample_advance
        expense = Expense.model_validate({
            "purpose": "Travel",
            "description": "Expense",
            "amount": Decimal("100.00"),
            "advance_id": sample_advance.id,
            "is_reconciled": False,
            "bills": [],
        })

        with pytest.raises(AppException) as exc:
            await expense_service.create_expense(employee_user, expense)

        assert exc.value.err_code == AppErr.EXPENSE_RECONCILE_PERMISSION_DENIED

    @pytest.mark.asyncio
    async def test_update_expense_success(self, expense_service, employee_user, sample_expense, mock_expense_repo):
        mock_expense_repo.get.return_value = sample_expense

        await expense_service.update_expense(employee_user, sample_expense)

        mock_expense_repo.update.assert_called_once_with(sample_expense)

    @pytest.mark.asyncio
    async def test_update_expense_not_found(self, expense_service, employee_user, sample_expense, mock_expense_repo):
        mock_expense_repo.get.return_value = None

        with pytest.raises(AppException) as exc:
            await expense_service.update_expense(employee_user, sample_expense)

        assert exc.value.err_code == AppErr.NOT_FOUND

    @pytest.mark.asyncio
    async def test_update_expense_forbidden(self, expense_service, employee_user, sample_expense, mock_expense_repo):
        sample_expense.user_id = "different-user-id"
        mock_expense_repo.get.return_value = sample_expense

        with pytest.raises(AppException) as exc:
            await expense_service.update_expense(employee_user, sample_expense)

        assert exc.value.err_code == AppErr.FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_all_expenses_employee(self, expense_service, employee_user, sample_expense, mock_expense_repo):
        mock_expense_repo.get_all.return_value = ([sample_expense], 1)
        filter_options = ExpensesFilterOptions(page=1, limit=10)

        expenses, total = await expense_service.get_all_expenses(employee_user, filter_options)

        assert len(expenses) == 1
        assert total == 1
        assert filter_options.user_id == employee_user.user_id

    @pytest.mark.asyncio
    async def test_get_all_expenses_admin(self, expense_service, admin_user, sample_expense, mock_expense_repo):
        mock_expense_repo.get_all.return_value = ([sample_expense], 1)
        filter_options = ExpensesFilterOptions(page=1, limit=10)

        expenses, total = await expense_service.get_all_expenses(admin_user, filter_options)

        assert len(expenses) == 1
        assert total == 1
        assert filter_options.user_id is None

    @pytest.mark.asyncio
    async def test_update_expense_status_approved(self, expense_service, sample_expense, mock_expense_repo):
        mock_expense_repo.get.return_value = sample_expense
        admin_id = uuid4().hex

        await expense_service.update_expense_status(admin_id, sample_expense.id, RequestStatus.Approved)

        assert sample_expense.status == RequestStatus.Approved
        assert sample_expense.approved_by == admin_id
        assert sample_expense.approved_at is not None
        mock_expense_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_expense_status_reviewed(self, expense_service, sample_expense, mock_expense_repo):
        mock_expense_repo.get.return_value = sample_expense
        reviewer_id = uuid4().hex

        await expense_service.update_expense_status(reviewer_id, sample_expense.id, RequestStatus.Reviewed)

        assert sample_expense.status == RequestStatus.Reviewed
        assert sample_expense.reviewed_by == reviewer_id
        assert sample_expense.reviewed_at is not None
        mock_expense_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_expense_status_not_found(self, expense_service, mock_expense_repo):
        mock_expense_repo.get.return_value = None

        with pytest.raises(AppException) as exc:
            await expense_service.update_expense_status(uuid4().hex, "non-existent-id", RequestStatus.Approved)

        assert exc.value.err_code == AppErr.NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_expense_summary_employee(self, expense_service, employee_user, mock_expense_repo):
        mock_expense_repo.get_sum.return_value = 1000.0

        summary = await expense_service.get_expense_summary(employee_user)

        assert summary.total_expense == Decimal("1000.0")
        assert summary.pending_expense == Decimal("1000.0")
        assert summary.reimbursed_expense == Decimal("1000.0")
        assert summary.rejected_expense == Decimal("1000.0")

    @pytest.mark.asyncio
    async def test_get_expense_summary_admin(self, expense_service, admin_user, mock_expense_repo):
        mock_expense_repo.get_sum.return_value = 5000.0

        summary = await expense_service.get_expense_summary(admin_user)

        assert summary.total_expense == Decimal("5000.0")
