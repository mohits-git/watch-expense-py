from uuid import uuid4
import pytest
import pytest_asyncio
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.models.image import ImageMetadata
from app.repository.image_metadata_repository import ImageMetadataRepository


class TestImageMetadataRepository:
    @pytest_asyncio.fixture(scope="class")
    async def image_repository(self, ddb_table, table_name):
        return ImageMetadataRepository(ddb_table, table_name)

    @pytest_asyncio.fixture(scope="class")
    async def user_id(self) -> str:
        return uuid4().hex

    @pytest_asyncio.fixture(scope="class")
    async def image_url(self) -> str:
        return f"https://example.com/images/{uuid4().hex}.jpg"

    @pytest_asyncio.fixture(scope="class")
    async def image_metadata(self, user_id):
        return ImageMetadata.model_validate({
            "user_id": user_id,
        })

    @pytest.mark.asyncio
    async def test_save(self, image_repository, image_url, image_metadata):
        await image_repository.save(image_url, image_metadata)

    @pytest.mark.asyncio
    async def test_save_image_already_exists(self, image_repository, image_url, image_metadata):
        with pytest.raises(AppException) as app_exc:
            await image_repository.save(image_url, image_metadata)
        assert app_exc.value.err_code == AppErr.IMAGE_URL_ALREADY_EXIST

    @pytest.mark.asyncio
    async def test_get(self, image_repository, image_url, image_metadata):
        result = await image_repository.get(image_url)
        assert result is not None
        assert result.user_id == image_metadata.user_id

    @pytest.mark.asyncio
    async def test_get_non_existent(self, image_repository):
        non_existent_url = "https://example.com/non-existent.jpg"
        result = await image_repository.get(non_existent_url)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, image_repository, image_url):
        await image_repository.delete(image_url)
        result = await image_repository.get(image_url)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_non_existent(self, image_repository):
        # Should NOT raise an error when deleting non-existent image
        non_existent_url = "https://example.com/another-non-existent.jpg"
        await image_repository.delete(non_existent_url)