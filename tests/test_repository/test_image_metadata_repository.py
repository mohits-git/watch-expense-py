from uuid import uuid4
import pytest
from unittest.mock import patch
from botocore.exceptions import ClientError
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.models.image import ImageMetadata
from app.repository.image_metadata_repository import ImageMetadataRepository


@pytest.fixture
def image_repository(mock_ddb_table, table_name):
    return ImageMetadataRepository(mock_ddb_table, table_name)


@pytest.fixture
def user_id():
    return uuid4().hex


@pytest.fixture
def image_url():
    return f"https://example.com/images/{uuid4().hex}.jpg"


@pytest.fixture
def image_metadata(user_id):
    return ImageMetadata(user_id=user_id)


class TestImageMetadataRepositorySave:
    @pytest.mark.asyncio
    async def test_save_success(self, image_repository, image_url, image_metadata, mock_ddb_table):
        mock_ddb_table.put_item.return_value = {}

        await image_repository.save(image_url, image_metadata)

        mock_ddb_table.put_item.assert_called_once()
        call_args = mock_ddb_table.put_item.call_args
        assert call_args.kwargs["Item"]["PK"] == "IMAGE"
        assert call_args.kwargs["Item"]["SK"] == f"IMAGE#{image_url}"
        assert call_args.kwargs["Item"]["UserID"] == image_metadata.user_id
        assert "ConditionExpression" in call_args.kwargs

    @pytest.mark.asyncio
    @patch("app.repository.utils.is_conditional_check_failure")
    async def test_save_image_already_exists(self, mock_is_conditional_check, image_repository, image_url, image_metadata, mock_ddb_table):
        error = ClientError(
            {"Error": {"Code": "ConditionalCheckFailedException"}},
            "PutItem"
        )
        mock_ddb_table.put_item.side_effect = error
        mock_is_conditional_check.return_value = True

        with pytest.raises(AppException) as exc_info:
            await image_repository.save(image_url, image_metadata)

        assert exc_info.value.err_code == AppErr.IMAGE_URL_ALREADY_EXIST
        mock_is_conditional_check.assert_called_once_with(error)

    @pytest.mark.asyncio
    @patch("app.repository.utils.handle_dynamo_error")
    @patch("app.repository.utils.is_conditional_check_failure")
    async def test_save_dynamo_error(self, mock_is_conditional_check, mock_handle_error, image_repository, image_url, image_metadata, mock_ddb_table):
        error = ClientError(
            {"Error": {"Code": "InternalServerError"}}, "PutItem")
        mock_ddb_table.put_item.side_effect = error
        mock_is_conditional_check.return_value = False
        mock_handle_error.side_effect = AppException(
            AppErr.INTERNAL, cause=error)

        with pytest.raises(AppException):
            await image_repository.save(image_url, image_metadata)

        mock_handle_error.assert_called_once_with(error)


class TestImageMetadataRepositoryGet:
    @pytest.mark.asyncio
    async def test_get_success(self, image_repository, image_url, user_id, mock_ddb_table):
        mock_ddb_table.get_item.return_value = {
            "Item": {
                "PK": "IMAGE",
                "SK": f"IMAGE#{image_url}",
                "UserID": user_id
            }
        }

        result = await image_repository.get(image_url)

        assert result is not None
        assert result.user_id == user_id
        mock_ddb_table.get_item.assert_called_once()
        call_args = mock_ddb_table.get_item.call_args
        assert call_args.kwargs["Key"]["PK"] == "IMAGE"
        assert call_args.kwargs["Key"]["SK"] == f"IMAGE#{image_url}"

    @pytest.mark.asyncio
    async def test_get_not_found(self, image_repository, image_url, mock_ddb_table):
        mock_ddb_table.get_item.return_value = {}

        result = await image_repository.get(image_url)

        assert result is None

    @pytest.mark.asyncio
    @patch("app.repository.utils.handle_dynamo_error")
    async def test_get_dynamo_error(self, mock_handle_error, image_repository, image_url, mock_ddb_table):
        error = ClientError(
            {"Error": {"Code": "InternalServerError"}}, "GetItem")
        mock_ddb_table.get_item.side_effect = error
        mock_handle_error.side_effect = AppException(
            AppErr.INTERNAL, cause=error)

        with pytest.raises(AppException):
            await image_repository.get(image_url)

        mock_handle_error.assert_called_once_with(error)


class TestImageMetadataRepositoryDelete:
    @pytest.mark.asyncio
    async def test_delete_success(self, image_repository, image_url, mock_ddb_table):
        mock_ddb_table.delete_item.return_value = {}

        await image_repository.delete(image_url)

        mock_ddb_table.delete_item.assert_called_once()
        call_args = mock_ddb_table.delete_item.call_args
        assert call_args.kwargs["Key"]["PK"] == "IMAGE"
        assert call_args.kwargs["Key"]["SK"] == f"IMAGE#{image_url}"

    @pytest.mark.asyncio
    @patch("app.repository.utils.handle_dynamo_error")
    async def test_delete_dynamo_error(self, mock_handle_error, image_repository, image_url, mock_ddb_table):
        error = ClientError(
            {"Error": {"Code": "InternalServerError"}}, "DeleteItem")
        mock_ddb_table.delete_item.side_effect = error
        mock_handle_error.side_effect = AppException(
            AppErr.INTERNAL, cause=error)

        with pytest.raises(AppException):
            await image_repository.delete(image_url)

        mock_handle_error.assert_called_once_with(error)
