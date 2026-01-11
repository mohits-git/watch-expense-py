from unittest.mock import MagicMock, AsyncMock
from io import BytesIO
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies.services import get_image_service
from app.errors.app_exception import AppException
from app.errors.codes import AppErr


@pytest.fixture
def mock_image_service():
    service = MagicMock()
    service.upload_image = AsyncMock()
    service.delete_image = AsyncMock()
    service.get_image_download_url = AsyncMock()
    return service


@pytest.fixture
def override_image_service(mock_image_service):
    app.dependency_overrides[get_image_service] = lambda: mock_image_service
    yield
    app.dependency_overrides.pop(get_image_service, None)


class TestUploadImage:
    def test_upload_image_success_as_employee(
        self,
        client: TestClient,
        mock_image_service: MagicMock,
        override_auth_employee,
        override_image_service,
    ):
        image_url = "https://s3.amazonaws.com/bucket/image123.jpg"
        mock_image_service.upload_image.return_value = image_url

        # Create a mock file
        file_content = b"fake image content"
        files = {"file": ("test_image.jpg", BytesIO(file_content), "image/jpeg")}

        response = client.post("/api/images/", files=files)

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["image_url"] == image_url
        assert data["message"] == "Image uploaded successfully"
        mock_image_service.upload_image.assert_called_once()

    def test_upload_image_as_admin_forbidden(
        self,
        client: TestClient,
        mock_image_service: MagicMock,
        override_auth_admin,
        override_image_service,
    ):
        file_content = b"fake image content"
        files = {"file": ("test_image.jpg", BytesIO(file_content), "image/jpeg")}

        response = client.post("/api/images/", files=files)

        assert response.status_code == 403
        mock_image_service.upload_image.assert_not_called()

    def test_upload_image_unauthorized(
        self,
        client: TestClient,
        mock_image_service: MagicMock,
        override_image_service,
        override_auth_unauthenticated,
    ):
        file_content = b"fake image content"
        files = {"file": ("test_image.jpg", BytesIO(file_content), "image/jpeg")}

        response = client.post("/api/images/", files=files)

        assert response.status_code == 401
        mock_image_service.upload_image.assert_not_called()

    def test_upload_image_no_file(
        self,
        client: TestClient,
        mock_image_service: MagicMock,
        override_auth_employee,
        override_image_service,
    ):
        response = client.post("/api/images/")

        assert response.status_code == 422
        mock_image_service.upload_image.assert_not_called()

    def test_upload_image_service_error(
        self,
        client: TestClient,
        mock_image_service: MagicMock,
        override_auth_employee,
        override_image_service,
    ):
        mock_image_service.upload_image.side_effect = AppException(
            AppErr.INTERNAL
        )

        file_content = b"fake image content"
        files = {"file": ("test_image.jpg", BytesIO(file_content), "image/jpeg")}

        response = client.post("/api/images/", files=files)

        assert response.status_code == 500


class TestDeleteImage:
    def test_delete_image_success_as_employee(
        self,
        client: TestClient,
        mock_image_service: MagicMock,
        override_auth_employee,
        override_image_service,
    ):
        mock_image_service.delete_image.return_value = None

        request_data = {
            "image_url": "https://s3.amazonaws.com/bucket/image123.jpg"
        }

        response = client.request(
            "DELETE",
            "/api/images/",
            json=request_data
        )

        assert response.status_code == 204
        mock_image_service.delete_image.assert_called_once()

    def test_delete_image_as_admin_forbidden(
        self,
        client: TestClient,
        mock_image_service: MagicMock,
        override_auth_admin,
        override_image_service,
    ):
        request_data = {
            "image_url": "https://s3.amazonaws.com/bucket/image123.jpg"
        }

        response = client.request("DELETE", "/api/images/", json=request_data)

        assert response.status_code == 403
        mock_image_service.delete_image.assert_not_called()

    def test_delete_image_not_found(
        self,
        client: TestClient,
        mock_image_service: MagicMock,
        override_auth_employee,
        override_image_service,
    ):
        mock_image_service.delete_image.side_effect = AppException(AppErr.IMAGE_NOT_FOUND)

        request_data = {
            "image_url": "https://s3.amazonaws.com/bucket/nonexistent.jpg"
        }

        response = client.request("DELETE", "/api/images/", json=request_data)

        assert response.status_code == 404

    def test_delete_image_unauthorized_access(
        self,
        client: TestClient,
        mock_image_service: MagicMock,
        override_auth_employee,
        override_image_service,
    ):
        mock_image_service.delete_image.side_effect = AppException(
            AppErr.UNAUTHORIZED_IMAGE_ACCESS
        )

        request_data = {
            "image_url": "https://s3.amazonaws.com/bucket/other_user_image.jpg"
        }

        response = client.request("DELETE", "/api/images/", json=request_data)

        assert response.status_code == 401

    def test_delete_image_validation_error(
        self,
        client: TestClient,
        mock_image_service: MagicMock,
        override_auth_employee,
        override_image_service,
    ):
        request_data = {}  # Missing imageUrl

        response = client.request("DELETE", "/api/images/", json=request_data)

        assert response.status_code == 422
        mock_image_service.delete_image.assert_not_called()

    def test_delete_image_unauthorized(
        self,
        client: TestClient,
        mock_image_service: MagicMock,
        override_image_service,
        override_auth_unauthenticated,
    ):
        request_data = {
            "image_url": "https://s3.amazonaws.com/bucket/image123.jpg"
        }

        response = client.request("DELETE", "/api/images/", json=request_data)

        assert response.status_code == 401
        mock_image_service.delete_image.assert_not_called()


class TestGetImageDownloadUrl:
    def test_get_download_url_success_as_owner(
        self,
        client: TestClient,
        mock_image_service: MagicMock,
        override_auth_employee,
        override_image_service,
    ):
        download_url = "https://s3.amazonaws.com/bucket/image123.jpg?signature=xyz"
        mock_image_service.get_image_download_url.return_value = download_url

        image_url = "https://s3.amazonaws.com/bucket/image123.jpg"

        response = client.get(
            "/api/images/download-url",
            params={"url": image_url}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["download_url"] == download_url
        assert data["message"] == "Success"
        mock_image_service.get_image_download_url.assert_called_once()

    def test_get_download_url_success_as_admin(
        self,
        client: TestClient,
        mock_image_service: MagicMock,
        override_auth_admin,
        override_image_service,
    ):
        download_url = "https://s3.amazonaws.com/bucket/image123.jpg?signature=xyz"
        mock_image_service.get_image_download_url.return_value = download_url

        image_url = "https://s3.amazonaws.com/bucket/image123.jpg"

        response = client.get(
            "/api/images/download-url",
            params={"url": image_url}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["download_url"] == download_url

    def test_get_download_url_not_found(
        self,
        client: TestClient,
        mock_image_service: MagicMock,
        override_auth_employee,
        override_image_service,
    ):
        mock_image_service.get_image_download_url.side_effect = AppException(
            AppErr.IMAGE_NOT_FOUND
        )

        image_url = "https://s3.amazonaws.com/bucket/nonexistent.jpg"

        response = client.get(
            "/api/images/download-url",
            params={"url": image_url}
        )

        assert response.status_code == 404

    def test_get_download_url_unauthorized_access(
        self,
        client: TestClient,
        mock_image_service: MagicMock,
        override_auth_employee,
        override_image_service,
    ):
        mock_image_service.get_image_download_url.side_effect = AppException(
            AppErr.UNAUTHORIZED_IMAGE_ACCESS
        )

        image_url = "https://s3.amazonaws.com/bucket/other_user_image.jpg"

        response = client.get(
            "/api/images/download-url",
            params={"url": image_url}
        )

        assert response.status_code == 401

    def test_get_download_url_missing_param(
        self,
        client: TestClient,
        mock_image_service: MagicMock,
        override_auth_employee,
        override_image_service,
    ):
        response = client.get("/api/images/download-url")

        assert response.status_code == 422
        mock_image_service.get_image_download_url.assert_not_called()

    def test_get_download_url_unauthorized(
        self,
        client: TestClient,
        mock_image_service: MagicMock,
        override_image_service,
        override_auth_unauthenticated,
    ):
        image_url = "https://s3.amazonaws.com/bucket/image123.jpg"

        response = client.get(
            "/api/images/download-url",
            params={"url": image_url}
        )

        assert response.status_code == 401
        mock_image_service.get_image_download_url.assert_not_called()
