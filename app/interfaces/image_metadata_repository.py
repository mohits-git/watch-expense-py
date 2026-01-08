from typing import Protocol

from app.models.image import ImageMetadata


class ImageRepository(Protocol):
    async def save_image_user_metadata(
        self, image_url: str, metadata: ImageMetadata) -> None: ...
    async def get_image_user_metadata(
        self, image_url: str) -> ImageMetadata | None: ...

    async def delete_image_user_metadata(self, image_url: str) -> None: ...
