from pydantic import BaseModel


class ImageUploadResponse(BaseModel):
    image_url: str


class DeleteImageRequest(BaseModel):
    image_url: str
