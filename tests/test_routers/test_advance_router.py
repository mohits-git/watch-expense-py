from unittest.mock import MagicMock, AsyncMock
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.advance import Advance, AdvanceSummary
from app.models.expense import RequestStatus
from app.dependencies.services import get_advance_service
from app.errors.app_exception import AppException
from app.errors.codes import AppErr


@pytest.fixture
def mock_advance_service():
    service = MagicMock()
    service.get_all_advances = AsyncMock()
    service.create_advance = AsyncMock()
    service.get_advance_summary = AsyncMock()
    service.get_advance_by_id = AsyncMock()
    service.update_advance = AsyncMock()
    service.update_advance_status = AsyncMock()
    return service


@pytest.fixture
def override_advance_service(mock_advance_service):
    app.dependency_overrides[get_advance_service] = lambda: mock_advance_service
    yield
    app.dependency_overrides.pop(get_advance_service, None)


@pytest.fixture
def sample_advance():
    return Advance.model_validate({
        "id": "advance-123",
        "user_id": "employee-user-id",
        "amount": Decimal("5000.00"),
        "description": "Travel advance for conference",
        "purpose": "Conference travel",
        "status": RequestStatus.Pending,
        "reconciled_expense_id": None,
        "approved_by": None,
        "approved_at": None,
        "reviewed_by": None,
        "reviewed_at": None,
        "created_at": 1704067200,
        "updated_at": 1704067200,
    })


@pytest.fixture
def sample_approved_advance():
    return Advance.model_validate({
        "id": "advance-456",
        "user_id": "employee-user-id",
        "amount": Decimal("3000.00"),
        "description": "Equipment purchase advance",
        "purpose": "Equipment",
        "status": RequestStatus.Approved,
        "reconciled_expense_id": None,
        "approved_by": "admin-user-id",
        "approved_at": 1704070800,
        "reviewed_by": None,
        "reviewed_at": None,
        "created_at": 1704067200,
        "updated_at": 1704070800,
    })


@pytest.fixture
def sample_advance_summary():
    return AdvanceSummary(
        approved=Decimal("10000.00"),
        reconciled=Decimal("5000.00"),
        pending=Decimal("3000.00"),
        rejected=Decimal("1000.00"),
    )


class TestGetAllAdvances:
    def test_get_all_advances_as_employee(
        self,
        client: TestClient,
        mock_advance_service: MagicMock,
        override_auth_employee,
        override_advance_service,
        sample_advance,
        sample_approved_advance,
    ):
        advances = [sample_advance, sample_approved_advance]
        mock_advance_service.get_all_advances.return_value = (advances, 2)

        response = client.get("/api/advance-request/")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["totalAdvances"] == 2
        assert len(data["data"]["advances"]) == 2
        assert data["data"]["advances"][0]["id"] == sample_advance.id
        mock_advance_service.get_all_advances.assert_called_once()

    def test_get_all_advances_as_admin(
        self,
        client: TestClient,
        mock_advance_service: MagicMock,
        override_auth_admin,
        override_advance_service,
        sample_advance,
    ):
        advances = [sample_advance]
        mock_advance_service.get_all_advances.return_value = (advances, 1)

        response = client.get("/api/advance-request/")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["totalAdvances"] == 1
        assert len(data["data"]["advances"]) == 1

    def test_get_all_advances_with_filters(
        self,
        client: TestClient,
        mock_advance_service: MagicMock,
        override_auth_admin,
        override_advance_service,
        sample_approved_advance,
    ):
        advances = [sample_approved_advance]
        mock_advance_service.get_all_advances.return_value = (advances, 1)

        response = client.get(
            "/api/advance-request/",
            params={"status": "APPROVED", "page": 1, "limit": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["totalAdvances"] == 1
        assert data["data"]["advances"][0]["status"] == "APPROVED"

    def test_get_all_advances_empty_list(
        self,
        client: TestClient,
        mock_advance_service: MagicMock,
        override_auth_employee,
        override_advance_service,
    ):
        mock_advance_service.get_all_advances.return_value = ([], 0)

        response = client.get("/api/advance-request/")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["totalAdvances"] == 0
        assert data["data"]["advances"] == []

    def test_get_all_advances_unauthorized(
        self,
        client: TestClient,
        mock_advance_service: MagicMock,
        override_advance_service,
        override_auth_unauthenticated,
    ):
        response = client.get("/api/advance-request/")

        assert response.status_code == 401


class TestCreateAdvance:
    def test_create_advance_success_as_employee(
        self,
        client: TestClient,
        mock_advance_service: MagicMock,
        override_auth_employee,
        override_advance_service,
    ):
        created_advance_id = "new-advance-id-123"
        mock_advance_service.create_advance.return_value = created_advance_id

        request_data = {
            "amount": 5000.00,
            "description": "Travel advance for conference",
            "purpose": "Conference travel",
        }

        response = client.post("/api/advance-request/", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["id"] == created_advance_id
        mock_advance_service.create_advance.assert_called_once()

    def test_create_advance_as_admin_forbidden(
        self,
        client: TestClient,
        mock_advance_service: MagicMock,
        override_auth_admin,
        override_advance_service,
    ):
        request_data = {
            "amount": 5000.00,
            "description": "Travel advance for conference",
            "purpose": "Conference travel",
        }

        response = client.post("/api/advance-request/", json=request_data)

        assert response.status_code == 403
        mock_advance_service.create_advance.assert_not_called()

    def test_create_advance_validation_error(
        self,
        client: TestClient,
        mock_advance_service: MagicMock,
        override_auth_employee,
        override_advance_service,
    ):
        request_data = {
            "amount": 5000.00,
            # Missing required fields
        }

        response = client.post("/api/advance-request/", json=request_data)

        assert response.status_code == 422
        mock_advance_service.create_advance.assert_not_called()

    def test_create_advance_negative_amount(
        self,
        client: TestClient,
        mock_advance_service: MagicMock,
        override_auth_employee,
        override_advance_service,
    ):
        request_data = {
            "amount": -1000.00,
            "description": "Travel advance",
            "purpose": "Travel",
        }

        response = client.post("/api/advance-request/", json=request_data)

        assert response.status_code == 422
        mock_advance_service.create_advance.assert_not_called()


class TestGetAdvanceSummary:
    def test_get_advance_summary_as_employee(
        self,
        client: TestClient,
        mock_advance_service: MagicMock,
        override_auth_employee,
        override_advance_service,
        sample_advance_summary,
    ):
        mock_advance_service.get_advance_summary.return_value = sample_advance_summary

        response = client.get("/api/advance-request/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["approved"] == 10000.00
        assert data["data"]["reconciled"] == 5000.00
        assert data["data"]["pendingReconciliation"] == 3000.00
        assert data["data"]["rejectedAdvance"] == 1000.00
        mock_advance_service.get_advance_summary.assert_called_once()

    def test_get_advance_summary_as_admin(
        self,
        client: TestClient,
        mock_advance_service: MagicMock,
        override_auth_admin,
        override_advance_service,
        sample_advance_summary,
    ):
        mock_advance_service.get_advance_summary.return_value = sample_advance_summary

        response = client.get("/api/advance-request/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["approved"] == 10000.00

    def test_get_advance_summary_unauthorized(
        self,
        client: TestClient,
        mock_advance_service: MagicMock,
        override_advance_service,
        override_auth_unauthenticated,
    ):
        response = client.get("/api/advance-request/summary")

        assert response.status_code == 401


class TestGetAdvanceById:
    def test_get_advance_by_id_as_owner(
        self,
        client: TestClient,
        mock_advance_service: MagicMock,
        override_auth_employee,
        override_advance_service,
        sample_advance,
    ):
        mock_advance_service.get_advance_by_id.return_value = sample_advance

        response = client.get(f"/api/advance-request/{sample_advance.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == sample_advance.id
        assert data["data"]["amount"] == float(sample_advance.amount)
        assert data["data"]["status"] == "PENDING"
        mock_advance_service.get_advance_by_id.assert_called_once()

    def test_get_advance_by_id_as_admin(
        self,
        client: TestClient,
        mock_advance_service: MagicMock,
        override_auth_admin,
        override_advance_service,
        sample_advance,
    ):
        mock_advance_service.get_advance_by_id.return_value = sample_advance

        response = client.get(f"/api/advance-request/{sample_advance.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == sample_advance.id

    def test_get_advance_by_id_not_found(
        self,
        client: TestClient,
        mock_advance_service: MagicMock,
        override_auth_employee,
        override_advance_service,
    ):
        mock_advance_service.get_advance_by_id.side_effect = AppException(AppErr.NOT_FOUND)

        response = client.get("/api/advance-request/non-existent-id")

        assert response.status_code == 404

    def test_get_advance_by_id_forbidden(
        self,
        client: TestClient,
        mock_advance_service: MagicMock,
        override_auth_employee,
        override_advance_service,
    ):
        mock_advance_service.get_advance_by_id.side_effect = AppException(AppErr.FORBIDDEN)

        response = client.get("/api/advance-request/other-user-advance")

        assert response.status_code == 403


class TestUpdateAdvance:
    def test_update_advance_success_as_owner(
        self,
        client: TestClient,
        mock_advance_service: MagicMock,
        override_auth_employee,
        override_advance_service,
        sample_advance,
    ):
        mock_advance_service.update_advance.return_value = None

        request_data = {
            "amount": 6000.00,
            "description": "Updated description",
            "purpose": "Updated purpose",
        }

        response = client.put(f"/api/advance-request/{sample_advance.id}", json=request_data)

        assert response.status_code == 200
        mock_advance_service.update_advance.assert_called_once()

    def test_update_advance_as_admin(
        self,
        client: TestClient,
        mock_advance_service: MagicMock,
        override_auth_admin,
        override_advance_service,
        sample_advance,
    ):
        mock_advance_service.update_advance.return_value = None

        request_data = {
            "amount": 6000.00,
            "description": "Updated by admin",
            "purpose": "Admin update",
        }

        response = client.put(f"/api/advance-request/{sample_advance.id}", json=request_data)

        assert response.status_code == 200
        mock_advance_service.update_advance.assert_called_once()

    def test_update_advance_not_found(
        self,
        client: TestClient,
        mock_advance_service: MagicMock,
        override_auth_employee,
        override_advance_service,
    ):
        mock_advance_service.update_advance.side_effect = AppException(AppErr.NOT_FOUND)

        request_data = {
            "amount": 6000.00,
            "description": "Updated description",
            "purpose": "Updated purpose",
        }

        response = client.put("/api/advance-request/non-existent-id", json=request_data)

        assert response.status_code == 404

    def test_update_advance_forbidden(
        self,
        client: TestClient,
        mock_advance_service: MagicMock,
        override_auth_employee,
        override_advance_service,
    ):
        mock_advance_service.update_advance.side_effect = AppException(AppErr.FORBIDDEN)

        request_data = {
            "amount": 6000.00,
            "description": "Updated description",
            "purpose": "Updated purpose",
        }

        response = client.put("/api/advance-request/other-user-advance", json=request_data)

        assert response.status_code == 403

    def test_update_advance_validation_error(
        self,
        client: TestClient,
        mock_advance_service: MagicMock,
        override_auth_employee,
        override_advance_service,
        sample_advance,
    ):
        request_data = {
            "amount": -1000.00,  # Invalid: negative amount
            "description": "Invalid update",
            "purpose": "Invalid",
        }

        response = client.put(f"/api/advance-request/{sample_advance.id}", json=request_data)

        assert response.status_code == 422
        mock_advance_service.update_advance.assert_not_called()


class TestUpdateAdvanceStatus:
    def test_update_advance_status_to_approved_as_admin(
        self,
        client: TestClient,
        mock_advance_service: MagicMock,
        override_auth_admin,
        override_advance_service,
    ):
        mock_advance_service.update_advance_status.return_value = None

        request_data = {
            "status": "APPROVED",
        }

        response = client.patch("/api/advance-request/advance-123", json=request_data)

        assert response.status_code == 200
        mock_advance_service.update_advance_status.assert_called_once()

    def test_update_advance_status_to_rejected_as_admin(
        self,
        client: TestClient,
        mock_advance_service: MagicMock,
        override_auth_admin,
        override_advance_service,
    ):
        mock_advance_service.update_advance_status.return_value = None

        request_data = {
            "status": "REJECTED",
        }

        response = client.patch("/api/advance-request/advance-123", json=request_data)

        assert response.status_code == 200
        mock_advance_service.update_advance_status.assert_called_once()

    def test_update_advance_status_as_employee_forbidden(
        self,
        client: TestClient,
        mock_advance_service: MagicMock,
        override_auth_employee,
        override_advance_service,
    ):
        request_data = {
            "status": "APPROVED",
        }

        response = client.patch("/api/advance-request/advance-123", json=request_data)

        assert response.status_code == 403
        mock_advance_service.update_advance_status.assert_not_called()

    def test_update_advance_status_not_found(
        self,
        client: TestClient,
        mock_advance_service: MagicMock,
        override_auth_admin,
        override_advance_service,
    ):
        mock_advance_service.update_advance_status.side_effect = AppException(AppErr.NOT_FOUND)

        request_data = {
            "status": "APPROVED",
        }

        response = client.patch("/api/advance-request/non-existent-id", json=request_data)

        assert response.status_code == 404

    def test_update_advance_status_invalid_status(
        self,
        client: TestClient,
        mock_advance_service: MagicMock,
        override_auth_admin,
        override_advance_service,
    ):
        request_data = {
            "status": "INVALID_STATUS",
        }

        response = client.patch("/api/advance-request/advance-123", json=request_data)

        assert response.status_code == 422
        mock_advance_service.update_advance_status.assert_not_called()
