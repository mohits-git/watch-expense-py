from io import BytesIO
from unittest.mock import MagicMock
import pytest
from botocore.exceptions import ClientError
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.infra.s3_image_store import S3ImageStore


class TestS3ImageStore:
    @pytest.fixture
    def bucket_name(self):
        return "test-bucket"

    @pytest.fixture
    def mock_s3_client(self):
        client = MagicMock()
        client.upload_fileobj = MagicMock()
        client.delete_object = MagicMock()
        client.generate_presigned_url = MagicMock()
        client.exceptions.NoSuchKey = type('NoSuchKey', (Exception,), {})
        return client

    @pytest.fixture
    def image_store(self, bucket_name, mock_s3_client):
        return S3ImageStore(bucket_name, mock_s3_client)

    @pytest.fixture
    def sample_image(self):
        return BytesIO(b"fake image data")

    @pytest.mark.asyncio
    async def test_upload_image_success(self, image_store, sample_image, mock_s3_client, bucket_name):
        result = await image_store.upload_image("test.jpg", sample_image)

        assert result is not None
        assert result.startswith(f"https://{bucket_name}.s3.amazonaws.com/")
        assert "test.jpg" in result
        mock_s3_client.upload_fileobj.assert_called_once()
        call_kwargs = mock_s3_client.upload_fileobj.call_args[1]
        assert call_kwargs['Bucket'] == bucket_name
        assert call_kwargs['Fileobj'] == sample_image

    @pytest.mark.asyncio
    async def test_upload_image_generates_unique_urls(self, image_store, sample_image):
        url1 = await image_store.upload_image("test.jpg", sample_image)
        sample_image.seek(0)  # Reset file pointer
        url2 = await image_store.upload_image("test.jpg", sample_image)

        assert url1 != url2

    @pytest.mark.asyncio
    async def test_upload_image_client_error(self, image_store, sample_image, mock_s3_client):
        error_response = {'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}}
        mock_s3_client.upload_fileobj.side_effect = ClientError(error_response, 'upload_fileobj')

        with pytest.raises(AppException) as exc:
            await image_store.upload_image("test.jpg", sample_image)

        assert exc.value.err_code == AppErr.IMAGE_UPLOAD_FAILED

    @pytest.mark.asyncio
    async def test_delete_image_success(self, image_store, mock_s3_client, bucket_name):
        image_url = f"https://{bucket_name}.s3.amazonaws.com/abc123_test.jpg"

        await image_store.delete_image(image_url)

        mock_s3_client.delete_object.assert_called_once()
        call_kwargs = mock_s3_client.delete_object.call_args[1]
        assert call_kwargs['Bucket'] == bucket_name
        assert call_kwargs['Key'] == "abc123_test.jpg"

    @pytest.mark.asyncio
    async def test_delete_image_not_found(self, image_store, mock_s3_client, bucket_name):
        image_url = f"https://{bucket_name}.s3.amazonaws.com/nonexistent.jpg"
        mock_s3_client.delete_object.side_effect = mock_s3_client.exceptions.NoSuchKey()

        with pytest.raises(AppException) as exc:
            await image_store.delete_image(image_url)

        assert exc.value.err_code == AppErr.IMAGE_NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_image_client_error(self, image_store, mock_s3_client, bucket_name):
        image_url = f"https://{bucket_name}.s3.amazonaws.com/test.jpg"
        error_response = {'Error': {'Code': 'InternalError', 'Message': 'Internal Error'}}
        mock_s3_client.delete_object.side_effect = ClientError(error_response, 'delete_object')

        with pytest.raises(AppException) as exc:
            await image_store.delete_image(image_url)

        assert exc.value.err_code == AppErr.IMAGE_DELETE_FAILED

    @pytest.mark.asyncio
    async def test_delete_image_invalid_url(self, image_store, bucket_name):
        invalid_url = f"https://{bucket_name}.s3.amazonaws.com/"

        with pytest.raises(AppException) as exc:
            await image_store.delete_image(invalid_url)

        assert exc.value.err_code == AppErr.IMAGE_URL_INVALID

    @pytest.mark.asyncio
    async def test_get_image_download_url_success(self, image_store, mock_s3_client, bucket_name):
        image_url = f"https://{bucket_name}.s3.amazonaws.com/abc123_test.jpg"
        presigned_url = "https://presigned-url.example.com?signature=xyz"
        mock_s3_client.generate_presigned_url.return_value = presigned_url

        result = await image_store.get_image_download_url(image_url)

        assert result == presigned_url
        mock_s3_client.generate_presigned_url.assert_called_once()
        call_kwargs = mock_s3_client.generate_presigned_url.call_args[1]
        assert call_kwargs['ClientMethod'] == 'get_object'
        assert call_kwargs['Params']['Bucket'] == bucket_name
        assert call_kwargs['Params']['Key'] == "abc123_test.jpg"
        assert call_kwargs['ExpiresIn'] == 60

    @pytest.mark.asyncio
    async def test_get_image_download_url_not_found(self, image_store, mock_s3_client, bucket_name):
        image_url = f"https://{bucket_name}.s3.amazonaws.com/nonexistent.jpg"
        mock_s3_client.generate_presigned_url.side_effect = mock_s3_client.exceptions.NoSuchKey()

        with pytest.raises(AppException) as exc:
            await image_store.get_image_download_url(image_url)

        assert exc.value.err_code == AppErr.IMAGE_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_image_download_url_client_error(self, image_store, mock_s3_client, bucket_name):
        image_url = f"https://{bucket_name}.s3.amazonaws.com/test.jpg"
        error_response = {'Error': {'Code': 'ServiceUnavailable', 'Message': 'Service Unavailable'}}
        mock_s3_client.generate_presigned_url.side_effect = ClientError(error_response, 'generate_presigned_url')

        with pytest.raises(AppException) as exc:
            await image_store.get_image_download_url(image_url)

        assert exc.value.err_code == AppErr.FAILED_TO_GET_DOWNLOAD_URL

    @pytest.mark.asyncio
    async def test_get_image_download_url_invalid_url(self, image_store, bucket_name):
        invalid_url = f"https://{bucket_name}.s3.amazonaws.com/"

        with pytest.raises(AppException) as exc:
            await image_store.get_image_download_url(invalid_url)

        assert exc.value.err_code == AppErr.IMAGE_URL_INVALID

    @pytest.mark.asyncio
    async def test_url_with_special_characters(self, image_store, bucket_name):
        image_url = f"https://{bucket_name}.s3.amazonaws.com/images/photo%20with%20spaces.jpg"

        await image_store.delete_image(image_url)

        call_kwargs = image_store._client.delete_object.call_args[1]
        assert call_kwargs['Key'] == "images/photo%20with%20spaces.jpg"

    @pytest.mark.asyncio
    async def test_url_with_nested_path(self, image_store, mock_s3_client, bucket_name):
        image_url = f"https://{bucket_name}.s3.amazonaws.com/users/123/profile/avatar.jpg"

        await image_store.delete_image(image_url)

        call_kwargs = mock_s3_client.delete_object.call_args[1]
        assert call_kwargs['Key'] == "users/123/profile/avatar.jpg"

    @pytest.mark.asyncio
    async def test_upload_different_file_types(self, image_store, mock_s3_client, bucket_name):
        file_types = ["image.png", "photo.jpeg", "document.pdf", "file.gif"]

        for filename in file_types:
            file_data = BytesIO(b"test data")
            url = await image_store.upload_image(filename, file_data)

            assert filename in url
            assert url.startswith(f"https://{bucket_name}.s3.amazonaws.com/")
