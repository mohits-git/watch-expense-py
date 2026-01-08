import uuid
import asyncio
from typing import IO
from botocore.exceptions import ClientError
from mypy_boto3_s3 import S3Client
from app.errors.app_exception import AppException
from app.errors.codes import AppErr


class S3ImageStore:
    def __init__(self, bucket_name: str, client: S3Client):
        self._bucket_name = bucket_name
        self._client = client

    def _build_obj_url(self, obj_key: str) -> str:
        return f"https://{self._bucket_name}.s3.amazonaws.com/{obj_key}"

    def _get_obj_key_from_url(self, image_url: str) -> str:
        prefix = f"https://{self._bucket_name}.s3.amazonaws.com/"
        key = image_url[len(prefix):]
        if not key:
            raise AppException(AppErr.IMAGE_URL_INVALID)
        return key

    async def upload_image(self, name: str, image: IO) -> str:
        try:
            obj_key = f"{uuid.uuid4().hex}_{name}"
            await asyncio.to_thread(lambda: self._client.upload_fileobj(
                Fileobj=image,
                Bucket=self._bucket_name,
                Key=obj_key,
            ))
            return self._build_obj_url(obj_key)
        except ClientError as e:
            raise AppException(AppErr.IMAGE_UPLOAD_FAILED, cause=e)

    async def delete_image(self, image_url: str) -> None:
        try:
            obj_key = self._get_obj_key_from_url(image_url)
            await asyncio.to_thread(lambda: self._client.delete_object(
                Bucket=self._bucket_name,
                Key=obj_key,
            ))
        except self._client.exceptions.NoSuchKey:
            raise AppException(AppErr.IMAGE_NOT_FOUND)
        except ClientError as e:
            raise AppException(AppErr.IMAGE_DELETE_FAILED, cause=e)

    async def get_image_download_url(self, image_url: str) -> str:
        try:
            obj_key = self._get_obj_key_from_url(image_url)
            presigned_url = await asyncio.to_thread(lambda: self._client.generate_presigned_url(
                ClientMethod='get_object',
                Params={
                    'Bucket': self._bucket_name,
                    'Key': obj_key,
                },
                ExpiresIn=60,  # URL valid for 1 minute
            ))
            return presigned_url
        except self._client.exceptions.NoSuchKey:
            raise AppException(AppErr.IMAGE_NOT_FOUND)
        except ClientError as e:
            raise AppException(AppErr.FAILED_TO_GET_DOWNLOAD_URL, cause=e)
