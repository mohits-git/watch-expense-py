from unittest.mock import MagicMock, AsyncMock
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.project import Project
from app.dependencies.services import get_project_service
from app.errors.app_exception import AppException
from app.errors.codes import AppErr


@pytest.fixture
def mock_project_service():
    service = MagicMock()
    service.get_all_projects = AsyncMock()
    service.create_project = AsyncMock()
    service.get_project_by_id = AsyncMock()
    service.update_project = AsyncMock()
    return service


@pytest.fixture
def override_project_service(mock_project_service):
    app.dependency_overrides[get_project_service] = lambda: mock_project_service
    yield
    app.dependency_overrides.pop(get_project_service, None)


@pytest.fixture
def sample_project():
    return Project.model_validate({
        "id": "project-123",
        "name": "Test Project",
        "description": "A test project description",
        "budget": Decimal("50000.00"),
        "start_date": 1704067200,  # 2024-01-01
        "end_date": 1735689600,    # 2024-12-31
        "department_id": "dept-123",
        "created_at": 1704067200,
        "updated_at": 1704067200,
    })


@pytest.fixture
def sample_project_2():
    return Project.model_validate({
        "id": "project-456",
        "name": "Another Project",
        "description": "Another test project",
        "budget": Decimal("75000.00"),
        "start_date": 1704067200,
        "end_date": 1735689600,
        "department_id": "dept-456",
        "created_at": 1704067200,
        "updated_at": 1704067200,
    })


class TestGetAllProjects:
    def test_get_all_projects_success_as_admin(
        self,
        client: TestClient,
        mock_project_service: MagicMock,
        override_auth_admin,
        override_project_service,
        sample_project,
        sample_project_2,
    ):
        projects = [sample_project, sample_project_2]
        mock_project_service.get_all_projects.return_value = projects

        response = client.get("/api/admin/projects/")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        assert data["data"][0]["id"] == sample_project.id
        assert data["data"][0]["name"] == sample_project.name
        assert data["data"][1]["id"] == sample_project_2.id
        mock_project_service.get_all_projects.assert_called_once()

    def test_get_all_projects_empty_list(
        self,
        client: TestClient,
        mock_project_service: MagicMock,
        override_auth_admin,
        override_project_service,
    ):
        mock_project_service.get_all_projects.return_value = []

        response = client.get("/api/admin/projects/")

        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []

    def test_get_all_projects_as_employee_forbidden(
        self,
        client: TestClient,
        mock_project_service: MagicMock,
        override_auth_employee,
        override_project_service,
    ):
        response = client.get("/api/admin/projects/")

        assert response.status_code == 403
        mock_project_service.get_all_projects.assert_not_called()

    def test_get_all_projects_unauthorized(
        self,
        client: TestClient,
        mock_project_service: MagicMock,
        override_project_service,
        override_auth_unauthenticated,
    ):
        response = client.get("/api/admin/projects/")

        assert response.status_code == 401


class TestCreateProject:
    def test_create_project_success_as_admin(
        self,
        client: TestClient,
        mock_project_service: MagicMock,
        override_auth_admin,
        override_project_service,
    ):
        created_project_id = "new-project-id-123"
        mock_project_service.create_project.return_value = created_project_id

        request_data = {
            "name": "New Project",
            "description": "A brand new project",
            "budget": 60000.00,
            "startDate": 1704067200,
            "endDate": 1735689600,
            "departmentId": "dept-123",
        }

        response = client.post("/api/admin/projects/", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["id"] == created_project_id
        mock_project_service.create_project.assert_called_once()

    def test_create_project_as_employee_forbidden(
        self,
        client: TestClient,
        mock_project_service: MagicMock,
        override_auth_employee,
        override_project_service,
    ):
        request_data = {
            "name": "New Project",
            "description": "A brand new project",
            "budget": 60000.00,
            "startDate": 1704067200,
            "endDate": 1735689600,
            "departmentId": "dept-123",
        }

        response = client.post("/api/admin/projects/", json=request_data)

        assert response.status_code == 403
        mock_project_service.create_project.assert_not_called()

    def test_create_project_validation_error(
        self,
        client: TestClient,
        mock_project_service: MagicMock,
        override_auth_admin,
        override_project_service,
    ):
        request_data = {
            # Missing required fields
            "name": "New Project",
        }

        response = client.post("/api/admin/projects/", json=request_data)

        assert response.status_code == 422
        mock_project_service.create_project.assert_not_called()

    def test_create_project_invalid_budget(
        self,
        client: TestClient,
        mock_project_service: MagicMock,
        override_auth_admin,
        override_project_service,
    ):
        request_data = {
            "name": "New Project",
            "description": "A brand new project",
            "budget": "invalid_budget",
            "startDate": 1704067200,
            "endDate": 1735689600,
            "departmentId": "dept-123",
        }

        response = client.post("/api/admin/projects/", json=request_data)

        assert response.status_code == 422
        mock_project_service.create_project.assert_not_called()


class TestGetProjectById:

    def test_get_project_by_id_success(
        self,
        client: TestClient,
        mock_project_service: MagicMock,
        override_auth_admin,
        override_project_service,
        sample_project,
    ):
        mock_project_service.get_project_by_id.return_value = sample_project

        response = client.get(f"/api/admin/projects/{sample_project.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == sample_project.id
        assert data["data"]["name"] == sample_project.name
        assert data["data"]["description"] == sample_project.description
        assert data["data"]["budget"] == float(sample_project.budget)
        mock_project_service.get_project_by_id.assert_called_once_with(sample_project.id)

    def test_get_project_by_id_not_found(
        self,
        client: TestClient,
        mock_project_service: MagicMock,
        override_auth_admin,
        override_project_service,
    ):
        mock_project_service.get_project_by_id.side_effect = AppException(AppErr.NOT_FOUND)

        response = client.get("/api/admin/projects/non-existent-id")

        assert response.status_code == 404

    def test_get_project_by_id_as_employee_forbidden(
        self,
        client: TestClient,
        mock_project_service: MagicMock,
        override_auth_employee,
        override_project_service,
    ):
        response = client.get("/api/admin/projects/some-project-id")

        assert response.status_code == 403
        mock_project_service.get_project_by_id.assert_not_called()


class TestUpdateProject:

    def test_update_project_success_as_admin(
        self,
        client: TestClient,
        mock_project_service: MagicMock,
        override_auth_admin,
        override_project_service,
        sample_project,
    ):
        mock_project_service.update_project.return_value = None

        request_data = {
            "name": "Updated Project Name",
            "description": "Updated description",
            "budget": 75000.00,
            "startDate": 1704067200,
            "endDate": 1735689600,
            "departmentId": "dept-456",
        }

        response = client.put(f"/api/admin/projects/{sample_project.id}", json=request_data)

        assert response.status_code == 200
        mock_project_service.update_project.assert_called_once()

    def test_update_project_as_employee_forbidden(
        self,
        client: TestClient,
        mock_project_service: MagicMock,
        override_auth_employee,
        override_project_service,
        sample_project,
    ):
        request_data = {
            "name": "Updated Project Name",
            "description": "Updated description",
            "budget": 75000.00,
            "startDate": 1704067200,
            "endDate": 1735689600,
            "departmentId": "dept-456",
        }

        response = client.put(f"/api/admin/projects/{sample_project.id}", json=request_data)

        assert response.status_code == 403
        mock_project_service.update_project.assert_not_called()

    def test_update_project_not_found(
        self,
        client: TestClient,
        mock_project_service: MagicMock,
        override_auth_admin,
        override_project_service,
    ):
        mock_project_service.update_project.side_effect = AppException(AppErr.NOT_FOUND)

        request_data = {
            "name": "Updated Project Name",
            "description": "Updated description",
            "budget": 75000.00,
            "startDate": 1704067200,
            "endDate": 1735689600,
            "departmentId": "dept-456",
        }

        response = client.put("/api/admin/projects/non-existent-id", json=request_data)

        assert response.status_code == 404

    def test_update_project_validation_error(
        self,
        client: TestClient,
        mock_project_service: MagicMock,
        override_auth_admin,
        override_project_service,
        sample_project,
    ):
        request_data = {
            "name": "Updated Name",
        }

        response = client.put(f"/api/admin/projects/{sample_project.id}", json=request_data)

        assert response.status_code == 422
        mock_project_service.update_project.assert_not_called()

    def test_update_project_partial_fields(
        self,
        client: TestClient,
        mock_project_service: MagicMock,
        override_auth_admin,
        override_project_service,
        sample_project,
    ):
        mock_project_service.update_project.return_value = None

        request_data = {
            "name": "Updated Name Only",
            "description": "Same description",
            "budget": 50000.00,
            "startDate": 1704067200,
            "endDate": 1735689600,
            "departmentId": "dept-123",
        }

        response = client.put(f"/api/admin/projects/{sample_project.id}", json=request_data)

        assert response.status_code == 200
        mock_project_service.update_project.assert_called_once()
