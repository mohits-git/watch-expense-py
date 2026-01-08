from typing import Protocol

from app.models.image import ImageMetadata


class ImageMetadataRepository(Protocol):
    async def save(
        self, image_url: str, metadata: ImageMetadata) -> None: ...
    async def get(
        self, image_url: str) -> ImageMetadata | None: ...

    async def delete(self, image_url: str) -> None: ...
