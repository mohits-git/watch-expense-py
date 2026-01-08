from types_aiobotocore_dynamodb.service_resource import Table
from botocore.exceptions import ClientError
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.models.image import ImageMetadata
from app.repository import utils


class ImageMetadataRepository:
    def __init__(self, ddb_table: Table, table_name: str):
        self._table_name = table_name
        self._table = ddb_table
        self._pk = "IMAGE"
        self._sk_prefix = "IMAGE#"

    def _get_primary_key(self, image_url: str) -> dict:
        return {
            "PK": self._pk,
            "SK": f"{self._sk_prefix}{image_url}"
        }

    async def save_image_user_metadata(self, image_url: str, metadata: ImageMetadata) -> None:
        try:
            primary_key = self._get_primary_key(image_url)
            await self._table.put_item(
                Item={
                    **primary_key,
                    **metadata.model_dump(by_alias=True)
                },
                ConditionExpression="attribute_not_exists(PK) AND attribute_not_exists(SK)",
            )
        except self._table.meta.client.exceptions.ConditionalCheckFailedException as err:
            raise AppException(AppErr.IMAGE_URL_ALREADY_EXIST, cause=err)
        except ClientError as err:
            raise utils.handle_dynamo_error(err)

    async def get_image_user_metadata(self, image_url: str) -> ImageMetadata | None:
        try:
            primary_key = self._get_primary_key(image_url)
            response = await self._table.get_item(Key={**primary_key})
            item = response.get("Item")
            if not item:
                return None
            return ImageMetadata.model_validate(item, by_alias=True)
        except ClientError as err:
            raise utils.handle_dynamo_error(err)

    async def delete_image_user_metadata(self, image_url: str) -> None:
        try:
            primary_key = self._get_primary_key(image_url)
            await self._table.delete_item(Key={**primary_key})
        except ClientError as err:
            raise utils.handle_dynamo_error(err)
