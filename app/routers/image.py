from typing import Annotated
from fastapi import APIRouter, Depends, File, UploadFile, status

from app.dependencies.auth import (
    AuthenticatedUser,
    authenticated_user,
    required_roles,
)
from app.dependencies.services import ImageServiceInstance
from app.dtos.image_upload import (
    DeleteImageRequest,
    ImageDownloadURLResponse,
    ImageUploadResponse,
)
from app.models.user import UserRole


image_router = APIRouter(
    prefix="/images", dependencies=[Depends(authenticated_user)])


@image_router.post(
    "/",
    status_code=201,
    response_model=ImageUploadResponse,
    dependencies=[Depends(required_roles([UserRole.Employee]))]
)
async def handle_upload_image(file: Annotated[UploadFile, File()],
                              curr_user: AuthenticatedUser,
                              image_service: ImageServiceInstance):
    if not file.filename:
        file.filename = "Untitled"
    image_url = await image_service.upload_image(
        curr_user, file.file, file.filename)
    return ImageUploadResponse(
        status=status.HTTP_201_CREATED,
        message="Image uploaded successfully",
        data=ImageUploadResponse.Data(image_url=image_url)
    )


@image_router.delete(
    "/",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(required_roles([UserRole.Employee]))]
)
async def handle_delete_image(
        image_delete_request: DeleteImageRequest,
        curr_user: AuthenticatedUser,
        image_service: ImageServiceInstance):
    await image_service.delete_image(
        curr_user,
        image_delete_request.image_url)


@image_router.get(
    "/download-url",
    response_model=ImageDownloadURLResponse
)
async def handle_get_download_url(
        url: str,
        curr_user: AuthenticatedUser,
        image_service: ImageServiceInstance):
    download_url = await image_service.get_image_download_url(
        curr_user,
        image_url=url
    )
    return ImageDownloadURLResponse(
        status=status.HTTP_200_OK,
        message="Success",
        data=ImageDownloadURLResponse.Data(download_url=download_url)
    )
