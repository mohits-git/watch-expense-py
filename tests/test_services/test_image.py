from io import BytesIO
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
import pytest
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.models.image import ImageMetadata
from app.models.user import UserClaims, UserRole
from app.services.image import ImageService


class TestImageService:
    @pytest.fixture
    def mock_image_metadata_repo(self):
        repo = MagicMock()
        repo.save = AsyncMock()
        repo.get = AsyncMock()
        repo.delete = AsyncMock()
        return repo

    @pytest.fixture
    def mock_image_store(self):
        store = MagicMock()
        store.upload_image = AsyncMock()
        store.delete_image = AsyncMock()
        store.get_image_download_url = AsyncMock()
        return store

    @pytest.fixture
    def image_service(self, mock_image_metadata_repo, mock_image_store):
        return ImageService(mock_image_metadata_repo, mock_image_store)

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
    def sample_image_data(self):
        return BytesIO(b"fake image data")

    @pytest.fixture
    def sample_image_metadata(self, employee_user):
        return ImageMetadata(UserID=employee_user.user_id)

    @pytest.mark.asyncio
    async def test_upload_image_success(self, image_service, employee_user, sample_image_data, mock_image_store, mock_image_metadata_repo):
        image_url = "https://example.com/images/test.jpg"
        mock_image_store.upload_image.return_value = image_url

        result = await image_service.upload_image(employee_user, sample_image_data, "test.jpg")

        assert result == image_url
        mock_image_store.upload_image.assert_called_once_with("test.jpg", sample_image_data)
        mock_image_metadata_repo.save.assert_called_once()
        saved_metadata = mock_image_metadata_repo.save.call_args[0][1]
        assert saved_metadata.user_id == employee_user.user_id

    @pytest.mark.asyncio
    async def test_delete_image_success(self, image_service, employee_user, sample_image_metadata, mock_image_metadata_repo, mock_image_store):
        image_url = "https://example.com/images/test.jpg"
        mock_image_metadata_repo.get.return_value = sample_image_metadata

        await image_service.delete_image(employee_user, image_url)

        mock_image_metadata_repo.get.assert_called_once_with(image_url)
        mock_image_store.delete_image.assert_called_once_with(image_url)
        mock_image_metadata_repo.delete.assert_called_once_with(image_url)

    @pytest.mark.asyncio
    async def test_delete_image_not_found(self, image_service, employee_user, mock_image_metadata_repo):
        image_url = "https://example.com/images/nonexistent.jpg"
        mock_image_metadata_repo.get.return_value = None

        with pytest.raises(AppException) as exc:
            await image_service.delete_image(employee_user, image_url)

        assert exc.value.err_code == AppErr.IMAGE_NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_image_unauthorized(self, image_service, employee_user, sample_image_metadata, mock_image_metadata_repo):
        image_url = "https://example.com/images/test.jpg"
        sample_image_metadata.user_id = "different-user-id"
        mock_image_metadata_repo.get.return_value = sample_image_metadata

        with pytest.raises(AppException) as exc:
            await image_service.delete_image(employee_user, image_url)

        assert exc.value.err_code == AppErr.UNAUTHORIZED_IMAGE_ACCESS

    @pytest.mark.asyncio
    async def test_get_image_download_url_success_own_image(self, image_service, employee_user, sample_image_metadata, mock_image_metadata_repo, mock_image_store):
        image_url = "https://example.com/images/test.jpg"
        download_url = "https://example.com/download/test.jpg?token=xyz"
        mock_image_metadata_repo.get.return_value = sample_image_metadata
        mock_image_store.get_image_download_url.return_value = download_url

        result = await image_service.get_image_download_url(employee_user, image_url)

        assert result == download_url
        mock_image_metadata_repo.get.assert_called_once_with(image_url)
        mock_image_store.get_image_download_url.assert_called_once_with(image_url)

    @pytest.mark.asyncio
    async def test_get_image_download_url_success_admin(self, image_service, admin_user, sample_image_metadata, mock_image_metadata_repo, mock_image_store):
        image_url = "https://example.com/images/test.jpg"
        download_url = "https://example.com/download/test.jpg?token=xyz"
        sample_image_metadata.user_id = "different-user-id"
        mock_image_metadata_repo.get.return_value = sample_image_metadata
        mock_image_store.get_image_download_url.return_value = download_url

        result = await image_service.get_image_download_url(admin_user, image_url)

        assert result == download_url

    @pytest.mark.asyncio
    async def test_get_image_download_url_not_found(self, image_service, employee_user, mock_image_metadata_repo):
        image_url = "https://example.com/images/nonexistent.jpg"
        mock_image_metadata_repo.get.return_value = None

        with pytest.raises(AppException) as exc:
            await image_service.get_image_download_url(employee_user, image_url)

        assert exc.value.err_code == AppErr.IMAGE_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_image_download_url_unauthorized(self, image_service, employee_user, sample_image_metadata, mock_image_metadata_repo):
        image_url = "https://example.com/images/test.jpg"
        sample_image_metadata.user_id = "different-user-id"
        mock_image_metadata_repo.get.return_value = sample_image_metadata

        with pytest.raises(AppException) as exc:
            await image_service.get_image_download_url(employee_user, image_url)

        assert exc.value.err_code == AppErr.UNAUTHORIZED_IMAGE_ACCESS

    @pytest.mark.asyncio
    async def test_get_image_download_url_cleanup_on_store_not_found(self, image_service, employee_user, sample_image_metadata, mock_image_metadata_repo, mock_image_store):
        image_url = "https://example.com/images/test.jpg"
        mock_image_metadata_repo.get.return_value = sample_image_metadata
        mock_image_store.get_image_download_url.side_effect = AppException(AppErr.IMAGE_NOT_FOUND)

        with pytest.raises(AppException) as exc:
            await image_service.get_image_download_url(employee_user, image_url)

        assert exc.value.err_code == AppErr.IMAGE_NOT_FOUND
        mock_image_metadata_repo.delete.assert_called_once_with(image_url)
