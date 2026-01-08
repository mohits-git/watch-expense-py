import asyncio
from typing import IO
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.models.user import UserClaims, UserRole
from app.models.image import ImageMetadata
from app.interfaces import ImageStore, ImageMetadataRepository


class ImageService:
    def __init__(self,
                 image_metadata_repo: ImageMetadataRepository,
                 image_store: ImageStore):
        self._metadata_repo = image_metadata_repo
        self._image_store = image_store

    async def upload_image(self, curr_user: UserClaims, image_data: IO, image_name: str):
        metadata = ImageMetadata(UserID=curr_user.user_id)
        image_url = await self._image_store.upload_image(image_name, image_data)
        await self._metadata_repo.save(image_url, metadata)
        return image_url

    async def delete_image(self, curr_user: UserClaims, image_url: str):
        metadata = await self._metadata_repo.get(image_url)
        if not metadata:
            raise AppException(AppErr.IMAGE_NOT_FOUND)
        if metadata.user_id != curr_user.user_id:
            raise AppException(AppErr.UNAUTHORIZED_IMAGE_ACCESS)
        await asyncio.gather(
            self._image_store.delete_image(image_url),
            self._metadata_repo.delete(image_url),
        )

    async def get_image_download_url(self, curr_user: UserClaims, image_url: str):
        metadata = await self._metadata_repo.get(image_url)
        if not metadata:
            raise AppException(AppErr.IMAGE_NOT_FOUND)
        if metadata.user_id != curr_user.user_id and curr_user.role != UserRole.Admin:
            raise AppException(AppErr.UNAUTHORIZED_IMAGE_ACCESS)
        try:
            download_url = await self._image_store.get_image_download_url(image_url)
            return download_url
        except AppException as e:
            if e.err_code == AppErr.IMAGE_NOT_FOUND:
                # If image not found in store, delete metadata as well
                await self._metadata_repo.delete(image_url)
            raise e
