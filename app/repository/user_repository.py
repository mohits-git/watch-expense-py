import asyncio
import uuid
import time

from botocore.exceptions import ClientError
from pydantic import ValidationError
from mypy_boto3_dynamodb.service_resource import Table
from mypy_boto3_dynamodb.type_defs import TransactWriteItemTypeDef
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.models.user import User
from boto3.dynamodb.conditions import Key
from app.repository import utils


class UserRepository:
    def __init__(self, ddb_table: Table, table_name: str):
        self._table = ddb_table
        self._table_name = table_name

    def _get_user_primary_key(self, user_id: str) -> dict:
        return {
            "PK": "USER",
            "SK": f"PROFILE#{user_id}",
        }

    def _get_lookup_primary_key(self, email: str) -> dict:
        return {"PK": "USER", "SK": f"EMAIL#{email}"}

    def _parse_user_item(self, item: dict) -> User:
        try:
            return User.model_validate(item, by_alias=True)
        except ValidationError as err:
            raise AppException(
                AppErr.INTERNAL,
                "Failed to parse user from database",
                cause=err,
            )

    async def _get_email_by_id(self, user_id) -> str | None:
        primary_key = self._get_user_primary_key(user_id)
        try:
            response = await asyncio.to_thread(lambda: self._table.get_item(
                Key={**primary_key}, ProjectionExpression="Email"
            ))
            if not response or "Item" not in response:
                return None
            return str(response["Item"]["Email"])
        except ClientError as err:
            raise utils.handle_dynamo_error(err)

    async def save(self, user: User) -> None:
        if not user.id:
            user.id = str(uuid.uuid4())
        if not user.created_at:
            user.created_at = int(time.time_ns() // 1e6)
            user.updated_at = user.created_at
        primary_key = self._get_user_primary_key(user.id)
        lookup_pk = self._get_lookup_primary_key(user.email)
        transact_items: list[TransactWriteItemTypeDef] = [
            {
                "Put": {
                    "TableName": self._table_name,
                    "Item": {
                        **primary_key,
                        **user.model_dump(by_alias=True),
                    },
                    "ConditionExpression": "attribute_not_exists(PK) AND attribute_not_exists(SK)",
                }
            },
            {
                "Put": {
                    "TableName": self._table_name,
                    "Item": {
                        **lookup_pk,
                        "UserID": user.id,
                    },
                    "ConditionExpression": "attribute_not_exists(PK) AND attribute_not_exists(SK)",
                }
            },
        ]
        try:
            await asyncio.to_thread(lambda: self._table.meta.client.transact_write_items(
                TransactItems=transact_items))
        except self._table.meta.client.exceptions.TransactionCanceledException as err:
            reasons = err.response.get("CancellationReasons", [])
            codes = {r.get("Code") for r in reasons}
            if "ConditionalCheckFailed" in codes:
                raise AppException(
                    AppErr.USER_ALREADY_EXISTS,
                    cause=err,
                )
            raise utils.handle_dynamo_error(err, "Failed to save user")
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to save user")

    async def get(self, user_id: str) -> User | None:
        try:
            primary_key = self._get_user_primary_key(user_id)
            response = await asyncio.to_thread(
                lambda: self._table.get_item(Key={**primary_key}))
            if not response or "Item" not in response:
                return None
            return self._parse_user_item(response["Item"])
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to fetch user")

    async def get_by_email(self, email: str) -> User | None:
        try:
            lookup_pk = self._get_lookup_primary_key(email)
            response = await asyncio.to_thread(
                lambda: self._table.get_item(Key={**lookup_pk}))
            if not response or "Item" not in response:
                return None
            user_id = str(response["Item"]["UserID"])
            return await self.get(user_id)
        except ClientError as err:
            raise utils.handle_dynamo_error(
                err, "Failed to fetch user by email")

    async def get_all(self) -> list[User]:
        try:
            response = await asyncio.to_thread(
                lambda: self._table.query(
                    KeyConditionExpression=Key("PK").eq("USER")
                    & Key("SK").begins_with("PROFILE#")
                )
            )
            if not response or "Items" not in response:
                return []
            users = [self._parse_user_item(item) for item in response["Items"]]
            return users
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to fetch users")

    async def delete(self, user_id: str) -> None:
        try:
            email = await self._get_email_by_id(user_id)
            if not email:
                raise AppException(
                    AppErr.NOT_FOUND,
                    "User not found")
            primary_key = self._get_user_primary_key(user_id)
            lookup_pk = self._get_lookup_primary_key(email)

            def batch_write():
                with self._table.batch_writer() as batch:
                    batch.delete_item(Key={**primary_key})
                    batch.delete_item(Key={**lookup_pk})
            await asyncio.to_thread(batch_write)
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to delete user")

    async def update(self, user: User) -> None:
        existing_email = await self._get_email_by_id(user.id)
        if not existing_email:
            raise AppException(
                AppErr.NOT_FOUND,
                "User not found")

        # build update expression
        user.updated_at = int(time.time_ns() // 1e6)
        exclude_fields = {"id", "created_at"}
        if not user.password or user.password == "":
            exclude_fields.add("password")
        to_update = user.model_dump(by_alias=True, exclude=exclude_fields)
        update_expr, expr_names, expr_values = utils.build_update_expression(
            to_update)

        primary_key = self._get_user_primary_key(user.id)
        if user.email == existing_email:
            try:
                await asyncio.to_thread(lambda: self._table.update_item(
                    Key=primary_key,
                    UpdateExpression=update_expr,
                    ExpressionAttributeNames=expr_names,
                    ExpressionAttributeValues=expr_values,
                    ConditionExpression="attribute_exists(PK) AND attribute_exists(SK)",
                ))
                return
            except ClientError as err:
                raise utils.handle_dynamo_error(err, "Failed to update user")

        lookup_pk = self._get_lookup_primary_key(existing_email)
        new_lookup_pk = self._get_lookup_primary_key(user.email)
        transact_items: list[TransactWriteItemTypeDef] = [
            {
                "Update": {
                    "TableName": self._table_name,
                    "Key": primary_key,
                    "UpdateExpression": update_expr,
                    "ExpressionAttributeNames": expr_names,
                    "ExpressionAttributeValues": expr_values,
                    "ConditionExpression": "attribute_exists(PK) AND attribute_exists(SK)",
                }
            },
            {
                "Delete": {
                    "TableName": self._table_name,
                    "Key": lookup_pk,
                }
            },
            {
                "Put": {
                    "TableName": self._table_name,
                    "Item": {**new_lookup_pk, "UserID": user.id},
                }
            }
        ]
        try:
            await asyncio.to_thread(
                lambda: self._table.meta.client.transact_write_items(
                    TransactItems=transact_items)
            )
        except self._table.meta.client.exceptions.TransactionCanceledException as err:
            reasons = err.response.get("CancellationReasons", [])
            codes = {r.get("Code") for r in reasons}
            if "ConditionalCheckFailed" in codes:
                raise AppException(
                    AppErr.NOT_FOUND,
                    "User not found",
                    cause=err,
                )
            raise AppException(
                AppErr.INTERNAL,
                "Failed to save user",
                cause=err,
            )
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to update user")
