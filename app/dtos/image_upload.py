from pydantic import BaseModel

from app.dtos.response import BaseResponse


class ImageUploadResponse(BaseResponse):
    class Data(BaseModel):
        image_url: str
    data: Data


class DeleteImageRequest(BaseModel):
    image_url: str


class ImageDownloadURLResponse(BaseResponse):
    class Data(BaseModel):
        download_url: str
    data: Data
