from unittest.mock import MagicMock, AsyncMock
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.expense import Expense, Bill, ExpenseSummary, RequestStatus
from app.dependencies.services import get_expense_service
from app.errors.app_exception import AppException
from app.errors.codes import AppErr


@pytest.fixture
def mock_expense_service():
    service = MagicMock()
    service.get_all_expenses = AsyncMock()
    service.create_expense = AsyncMock()
    service.get_expense_summary = AsyncMock()
    service.get_expense_by_id = AsyncMock()
    service.update_expense = AsyncMock()
    service.update_expense_status = AsyncMock()
    return service


@pytest.fixture
def override_expense_service(mock_expense_service):
    app.dependency_overrides[get_expense_service] = lambda: mock_expense_service
    yield
    app.dependency_overrides.pop(get_expense_service, None)


@pytest.fixture
def sample_bill():
    return Bill.model_validate({
        "id": "bill-123",
        "amount": Decimal("1500.00"),
        "description": "Hotel bill",
        "attachment_url": "https://example.com/bill1.pdf",
    })


@pytest.fixture
def sample_expense(sample_bill):
    return Expense.model_validate({
        "id": "expense-123",
        "user_id": "employee-user-id",
        "amount": Decimal("5000.00"),
        "description": "Business travel expenses",
        "purpose": "Client meeting",
        "status": RequestStatus.Pending,
        "is_reconciled": False,
        "advance_id": None,
        "approved_by": None,
        "approved_at": None,
        "reviewed_by": None,
        "reviewed_at": None,
        "bills": [sample_bill],
        "created_at": 1704067200,
        "updated_at": 1704067200,
    })


@pytest.fixture
def sample_approved_expense():
    return Expense.model_validate({
        "id": "expense-456",
        "user_id": "employee-user-id",
        "amount": Decimal("3000.00"),
        "description": "Equipment purchase",
        "purpose": "Office supplies",
        "status": RequestStatus.Approved,
        "is_reconciled": False,
        "advance_id": None,
        "approved_by": "admin-user-id",
        "approved_at": 1704070800,
        "reviewed_by": None,
        "reviewed_at": None,
        "bills": [],
        "created_at": 1704067200,
        "updated_at": 1704070800,
    })


@pytest.fixture
def sample_expense_summary():
    return ExpenseSummary(
        total_expense=Decimal("20000.00"),
        pending_expense=Decimal("5000.00"),
        reimbursed_expense=Decimal("12000.00"),
        rejected_expense=Decimal("3000.00"),
    )


class TestGetAllExpenses:
    def test_get_all_expenses_as_employee(
        self,
        client: TestClient,
        mock_expense_service: MagicMock,
        override_auth_employee,
        override_expense_service,
        sample_expense,
        sample_approved_expense,
    ):
        expenses = [sample_expense, sample_approved_expense]
        mock_expense_service.get_all_expenses.return_value = (expenses, 2)

        response = client.get("/api/expenses/")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["totalExpenses"] == 2
        assert len(data["data"]["expenses"]) == 2
        assert data["data"]["expenses"][0]["id"] == sample_expense.id
        mock_expense_service.get_all_expenses.assert_called_once()

    def test_get_all_expenses_as_admin(
        self,
        client: TestClient,
        mock_expense_service: MagicMock,
        override_auth_admin,
        override_expense_service,
        sample_expense,
    ):
        expenses = [sample_expense]
        mock_expense_service.get_all_expenses.return_value = (expenses, 1)

        response = client.get("/api/expenses/")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["totalExpenses"] == 1
        assert len(data["data"]["expenses"]) == 1

    def test_get_all_expenses_with_filters(
        self,
        client: TestClient,
        mock_expense_service: MagicMock,
        override_auth_admin,
        override_expense_service,
        sample_approved_expense,
    ):
        expenses = [sample_approved_expense]
        mock_expense_service.get_all_expenses.return_value = (expenses, 1)

        response = client.get(
            "/api/expenses/",
            params={"status": "APPROVED", "page": 1, "limit": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["totalExpenses"] == 1
        assert data["data"]["expenses"][0]["status"] == "APPROVED"

    def test_get_all_expenses_empty_list(
        self,
        client: TestClient,
        mock_expense_service: MagicMock,
        override_auth_employee,
        override_expense_service,
    ):
        mock_expense_service.get_all_expenses.return_value = ([], 0)

        response = client.get("/api/expenses/")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["totalExpenses"] == 0
        assert data["data"]["expenses"] == []

    def test_get_all_expenses_unauthorized(
        self,
        client: TestClient,
        mock_expense_service: MagicMock,
        override_expense_service,
        override_auth_unauthenticated,
    ):
        response = client.get("/api/expenses/")

        assert response.status_code == 401


class TestCreateExpense:
    def test_create_expense_success_as_employee(
        self,
        client: TestClient,
        mock_expense_service: MagicMock,
        override_auth_employee,
        override_expense_service,
    ):
        created_expense_id = "new-expense-id-123"
        mock_expense_service.create_expense.return_value = created_expense_id

        request_data = {
            "amount": 5000.00,
            "description": "Business travel expenses",
            "purpose": "Client meeting",
            "bills": [
                {
                    "amount": 1500.00,
                    "description": "Hotel bill",
                    "attachmentUrl": "https://example.com/bill1.pdf"
                }
            ],
            "isReconciled": False,
        }

        response = client.post("/api/expenses/", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["id"] == created_expense_id
        mock_expense_service.create_expense.assert_called_once()

    def test_create_expense_with_advance_id(
        self,
        client: TestClient,
        mock_expense_service: MagicMock,
        override_auth_employee,
        override_expense_service,
    ):
        created_expense_id = "new-expense-id-456"
        mock_expense_service.create_expense.return_value = created_expense_id

        request_data = {
            "amount": 3000.00,
            "description": "Reconciled expense",
            "purpose": "Advance reconciliation",
            "bills": [],
            "isReconciled": True,
            "advanceId": "advance-123",
        }

        response = client.post("/api/expenses/", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["id"] == created_expense_id

    def test_create_expense_as_admin_forbidden(
        self,
        client: TestClient,
        mock_expense_service: MagicMock,
        override_auth_admin,
        override_expense_service,
    ):
        request_data = {
            "amount": 5000.00,
            "description": "Business travel expenses",
            "purpose": "Client meeting",
            "bills": [],
            "isReconciled": False,
        }

        response = client.post("/api/expenses/", json=request_data)

        assert response.status_code == 403
        mock_expense_service.create_expense.assert_not_called()

    def test_create_expense_validation_error(
        self,
        client: TestClient,
        mock_expense_service: MagicMock,
        override_auth_employee,
        override_expense_service,
    ):
        request_data = {
            "amount": 5000.00,
            # Missing required fields
        }

        response = client.post("/api/expenses/", json=request_data)

        assert response.status_code == 422
        mock_expense_service.create_expense.assert_not_called()

    def test_create_expense_negative_amount(
        self,
        client: TestClient,
        mock_expense_service: MagicMock,
        override_auth_employee,
        override_expense_service,
    ):
        request_data = {
            "amount": -1000.00,
            "description": "Invalid expense",
            "purpose": "Invalid",
            "bills": [],
            "isReconciled": False,
        }

        response = client.post("/api/expenses/", json=request_data)

        assert response.status_code == 422
        mock_expense_service.create_expense.assert_not_called()

    def test_create_expense_invalid_advance_id(
        self,
        client: TestClient,
        mock_expense_service: MagicMock,
        override_auth_employee,
        override_expense_service,
    ):
        mock_expense_service.create_expense.side_effect = AppException(
            AppErr.INVALID_EXPENSE_RECONCILE_ADVANCE
        )

        request_data = {
            "amount": 3000.00,
            "description": "Reconciled expense",
            "purpose": "Advance reconciliation",
            "bills": [],
            "isReconciled": True,
            "advanceId": "invalid-advance-id",
        }

        response = client.post("/api/expenses/", json=request_data)

        assert response.status_code == 422


class TestGetExpenseSummary:
    def test_get_expense_summary_as_employee(
        self,
        client: TestClient,
        mock_expense_service: MagicMock,
        override_auth_employee,
        override_expense_service,
        sample_expense_summary,
    ):
        mock_expense_service.get_expense_summary.return_value = sample_expense_summary

        response = client.get("/api/expenses/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["totalExpense"] == 20000.00
        assert data["data"]["pendingExpense"] == 5000.00
        assert data["data"]["reimbursedExpense"] == 12000.00
        assert data["data"]["rejectedExpense"] == 3000.00
        mock_expense_service.get_expense_summary.assert_called_once()

    def test_get_expense_summary_as_admin(
        self,
        client: TestClient,
        mock_expense_service: MagicMock,
        override_auth_admin,
        override_expense_service,
        sample_expense_summary,
    ):
        mock_expense_service.get_expense_summary.return_value = sample_expense_summary

        response = client.get("/api/expenses/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["totalExpense"] == 20000.00

    def test_get_expense_summary_unauthorized(
        self,
        client: TestClient,
        mock_expense_service: MagicMock,
        override_expense_service,
        override_auth_unauthenticated,
    ):
        response = client.get("/api/expenses/summary")

        assert response.status_code == 401


class TestGetExpenseById:
    def test_get_expense_by_id_as_owner(
        self,
        client: TestClient,
        mock_expense_service: MagicMock,
        override_auth_employee,
        override_expense_service,
        sample_expense,
    ):
        mock_expense_service.get_expense_by_id.return_value = sample_expense

        response = client.get(f"/api/expenses/{sample_expense.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == sample_expense.id
        assert data["data"]["amount"] == float(sample_expense.amount)
        assert data["data"]["status"] == "PENDING"
        assert len(data["data"]["bills"]) == 1
        mock_expense_service.get_expense_by_id.assert_called_once()

    def test_get_expense_by_id_as_admin(
        self,
        client: TestClient,
        mock_expense_service: MagicMock,
        override_auth_admin,
        override_expense_service,
        sample_expense,
    ):
        mock_expense_service.get_expense_by_id.return_value = sample_expense

        response = client.get(f"/api/expenses/{sample_expense.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == sample_expense.id

    def test_get_expense_by_id_not_found(
        self,
        client: TestClient,
        mock_expense_service: MagicMock,
        override_auth_employee,
        override_expense_service,
    ):
        mock_expense_service.get_expense_by_id.side_effect = AppException(AppErr.NOT_FOUND)

        response = client.get("/api/expenses/non-existent-id")

        assert response.status_code == 404

    def test_get_expense_by_id_forbidden(
        self,
        client: TestClient,
        mock_expense_service: MagicMock,
        override_auth_employee,
        override_expense_service,
    ):
        mock_expense_service.get_expense_by_id.side_effect = AppException(AppErr.FORBIDDEN)

        response = client.get("/api/expenses/other-user-expense")

        assert response.status_code == 403


class TestUpdateExpense:
    def test_update_expense_success_as_admin(
        self,
        client: TestClient,
        mock_expense_service: MagicMock,
        override_auth_admin,
        override_expense_service,
        sample_expense,
    ):
        mock_expense_service.update_expense.return_value = None

        request_data = {
            "amount": 6000.00,
            "description": "Updated description",
            "purpose": "Updated purpose",
            "bills": [],
            "isReconciled": False,
        }

        response = client.put(f"/api/expenses/{sample_expense.id}", json=request_data)

        assert response.status_code == 200
        mock_expense_service.update_expense.assert_called_once()

    def test_update_expense_as_employee_forbidden(
        self,
        client: TestClient,
        mock_expense_service: MagicMock,
        override_auth_employee,
        override_expense_service,
        sample_expense,
    ):
        request_data = {
            "amount": 6000.00,
            "description": "Updated description",
            "purpose": "Updated purpose",
            "bills": [],
            "isReconciled": False,
        }

        response = client.put(f"/api/expenses/{sample_expense.id}", json=request_data)

        assert response.status_code == 403
        mock_expense_service.update_expense.assert_not_called()

    def test_update_expense_not_found(
        self,
        client: TestClient,
        mock_expense_service: MagicMock,
        override_auth_admin,
        override_expense_service,
    ):
        mock_expense_service.update_expense.side_effect = AppException(AppErr.NOT_FOUND)

        request_data = {
            "amount": 6000.00,
            "description": "Updated description",
            "purpose": "Updated purpose",
            "bills": [],
            "isReconciled": False,
        }

        response = client.put("/api/expenses/non-existent-id", json=request_data)

        assert response.status_code == 404

    def test_update_expense_validation_error(
        self,
        client: TestClient,
        mock_expense_service: MagicMock,
        override_auth_admin,
        override_expense_service,
        sample_expense,
    ):
        request_data = {
            "amount": -1000.00,  # Invalid: negative amount
            "description": "Invalid update",
            "purpose": "Invalid",
            "bills": [],
            "isReconciled": False,
        }

        response = client.put(f"/api/expenses/{sample_expense.id}", json=request_data)

        assert response.status_code == 422
        mock_expense_service.update_expense.assert_not_called()


class TestUpdateExpenseStatus:
    def test_update_expense_status_to_approved_as_admin(
        self,
        client: TestClient,
        mock_expense_service: MagicMock,
        override_auth_admin,
        override_expense_service,
    ):
        mock_expense_service.update_expense_status.return_value = None

        request_data = {
            "status": "APPROVED",
        }

        response = client.patch("/api/expenses/expense-123", json=request_data)

        assert response.status_code == 200
        mock_expense_service.update_expense_status.assert_called_once()

    def test_update_expense_status_to_rejected_as_admin(
        self,
        client: TestClient,
        mock_expense_service: MagicMock,
        override_auth_admin,
        override_expense_service,
    ):
        mock_expense_service.update_expense_status.return_value = None

        request_data = {
            "status": "REJECTED",
        }

        response = client.patch("/api/expenses/expense-123", json=request_data)

        assert response.status_code == 200
        mock_expense_service.update_expense_status.assert_called_once()

    def test_update_expense_status_as_employee_forbidden(
        self,
        client: TestClient,
        mock_expense_service: MagicMock,
        override_auth_employee,
        override_expense_service,
    ):
        request_data = {
            "status": "APPROVED",
        }

        response = client.patch("/api/expenses/expense-123", json=request_data)

        assert response.status_code == 403
        mock_expense_service.update_expense_status.assert_not_called()

    def test_update_expense_status_not_found(
        self,
        client: TestClient,
        mock_expense_service: MagicMock,
        override_auth_admin,
        override_expense_service,
    ):
        mock_expense_service.update_expense_status.side_effect = AppException(AppErr.NOT_FOUND)

        request_data = {
            "status": "APPROVED",
        }

        response = client.patch("/api/expenses/non-existent-id", json=request_data)

        assert response.status_code == 404

    def test_update_expense_status_invalid_status(
        self,
        client: TestClient,
        mock_expense_service: MagicMock,
        override_auth_admin,
        override_expense_service,
    ):
        request_data = {
            "status": "INVALID_STATUS",
        }

        response = client.patch("/api/expenses/expense-123", json=request_data)

        assert response.status_code == 422
        mock_expense_service.update_expense_status.assert_not_called()
