import asyncio
import uuid
import time

from botocore.exceptions import ClientError
from pydantic import ValidationError
from mypy_boto3_dynamodb.service_resource import Table
from mypy_boto3_dynamodb.type_defs import QueryInputTableQueryTypeDef, TransactWriteItemTypeDef
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.models.user import User
from boto3.dynamodb.conditions import Key
from app.repository import utils


class UserRepository:
    def __init__(self, ddb_table: Table, table_name: str):
        self._table = ddb_table
        self._table_name = table_name
        self._user_pk_prefix = "USER"
        self._user_profile_sk_prefix = "PROFILE"

    def _get_primary_key(
            self, *,
            user_id: str | None = None,
            email: str | None = None,
    ) -> dict:
        suffix = ""
        if user_id:
            suffix = f"#{user_id}"
        elif email:
            suffix = f"#{email}"
        return {
            "PK": f"{self._user_pk_prefix}{suffix}",
            "SK": f"{self._user_profile_sk_prefix}",
        }

    def _get_fetch_all_primary_key(
        self, *,
        user_id: str | None = None,
        created_at: int | None = None,
    ) -> dict:
        sk_suffix = ""
        if created_at:
            sk_suffix = f"#{created_at}"
            if user_id:
                sk_suffix = f"{sk_suffix}#{user_id}"
        return {
            "PK": f"{self._user_pk_prefix}",
            "SK": f"{self._user_profile_sk_prefix}{sk_suffix}",
        }

    def _parse_user_item(self, item: dict) -> User:
        try:
            return User.model_validate(item, by_alias=True, extra="ignore")
        except ValidationError as err:
            raise AppException(
                AppErr.INTERNAL,
                "Failed to parse user from database",
                cause=err,
            )

    async def save(self, user: User) -> None:
        if not user.id:
            user.id = str(uuid.uuid4())
        if not user.created_at:
            user.created_at = int(time.time_ns() // 1e6)
            user.updated_at = user.created_at

        user_id_primary_key = self._get_primary_key(user_id=user.id)
        email_primary_key = self._get_primary_key(email=user.email)
        fetch_all_primary_key = self._get_fetch_all_primary_key(
            created_at=user.created_at, user_id=user.id)

        transact_items: list[TransactWriteItemTypeDef] = [
            {
                "Put": {
                    "TableName": self._table_name,
                    "Item": {
                        **user_id_primary_key,
                        **user.model_dump(by_alias=True),
                    },
                    "ConditionExpression": "attribute_not_exists(PK)",
                }
            },
            {
                "Put": {
                    "TableName": self._table_name,
                    "Item": {
                        **email_primary_key,
                        **user.model_dump(by_alias=True),
                    },
                    "ConditionExpression": "attribute_not_exists(PK)",
                }
            },
            {
                "Put": {
                    "TableName": self._table_name,
                    "Item": {
                        **fetch_all_primary_key,
                        **user.model_dump(by_alias=True),
                    },
                }
            },
        ]
        try:
            await asyncio.to_thread(lambda: self._table.meta.client.transact_write_items(
                TransactItems=transact_items))
        except ClientError as err:
            if utils.is_conditional_check_failure(err):
                raise AppException(AppErr.USER_ALREADY_EXISTS, cause=err)
            raise utils.handle_dynamo_error(err, "Failed to save user")

    async def _get_user_by_pk(self, primary_key: dict) -> User | None:
        try:
            response = await asyncio.to_thread(
                lambda: self._table.get_item(Key={**primary_key}))
            if not response or "Item" not in response:
                return None
            return self._parse_user_item(response["Item"])
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to fetch user")

    async def get(self, user_id: str) -> User | None:
        primary_key = self._get_primary_key(user_id=user_id)
        return await self._get_user_by_pk(primary_key)

    async def get_by_email(self, email: str) -> User | None:
        primary_key = self._get_primary_key(email=email)
        return await self._get_user_by_pk(primary_key)

    async def get_all(self) -> list[User]:
        try:
            fetch_all_pk = self._get_fetch_all_primary_key()
            query_input: QueryInputTableQueryTypeDef = {
                "KeyConditionExpression": Key("PK").eq(fetch_all_pk["PK"]),
            }
            items = await utils.query_items(self._table, query_input)
            users = [self._parse_user_item(item) for item in items]
            return users
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to fetch users")

    async def delete(self, user_id: str) -> None:
        try:
            existing_user = await self.get(user_id)
            if existing_user is None:
                raise AppException(
                    AppErr.NOT_FOUND,
                    "User not found")
            primary_key = self._get_primary_key(user_id=existing_user.id)
            email_primary_key = self._get_primary_key(
                email=existing_user.email)
            fetch_all_primary_key = self._get_fetch_all_primary_key(
                user_id=existing_user.id, created_at=existing_user.created_at)

            def batch_write():
                with self._table.batch_writer() as batch:
                    batch.delete_item(Key={**primary_key})
                    batch.delete_item(Key={**email_primary_key})
                    batch.delete_item(Key={**fetch_all_primary_key})

            await asyncio.to_thread(batch_write)
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to delete user")

    async def update(self, user: User) -> None:
        existing_user = await self.get(user.id)
        if existing_user is None:
            raise AppException(
                AppErr.NOT_FOUND,
                "User not found")
        existing_email = existing_user.email

        # build update expression
        user.updated_at = int(time.time_ns() // 1e6)
        exclude_fields = {"id", "created_at"}
        if not user.password or user.password == "":
            exclude_fields.add("password")
        to_update = user.model_dump(by_alias=True, exclude=exclude_fields)
        update_expr, expr_names, expr_values = utils.build_update_expression(
            to_update)

        primary_key = self._get_primary_key(user_id=existing_user.id)
        email_primary_key = self._get_primary_key(email=existing_user.email)
        fetch_all_primary_key = self._get_fetch_all_primary_key(
            user_id=user.id, created_at=existing_user.created_at)

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
                "Update": {
                    "TableName": self._table_name,
                    "Key": fetch_all_primary_key,
                    "UpdateExpression": update_expr,
                    "ExpressionAttributeNames": expr_names,
                    "ExpressionAttributeValues": expr_values,
                    "ConditionExpression": "attribute_exists(PK) AND attribute_exists(SK)",
                }
            }
        ]

        if user.email != existing_email:
            new_email_primary_key = self._get_primary_key(email=user.email)
            transact_items.append({
                "Delete": {
                    "TableName": self._table_name,
                    "Key": email_primary_key,
                },
            })
            transact_items.append({
                "Put": {
                    "TableName": self._table_name,
                    "Item": {
                        **new_email_primary_key,
                        **user.model_dump(by_alias=True),
                    },
                    "ConditionExpression": "attribute_not_exists(PK)",
                }
            })
        else:
            transact_items.append({
                "Update": {
                    "TableName": self._table_name,
                    "Key": email_primary_key,
                    "UpdateExpression": update_expr,
                    "ExpressionAttributeNames": expr_names,
                    "ExpressionAttributeValues": expr_values,
                    "ConditionExpression": "attribute_exists(PK) AND attribute_exists(SK)",
                }
            })

        try:
            await asyncio.to_thread(
                lambda: self._table.meta.client.transact_write_items(
                    TransactItems=transact_items)
            )
        except ClientError as err:
            if utils.is_conditional_check_failure(err):
                raise AppException(
                    AppErr.NOT_FOUND,
                    "User not found",
                    cause=err)
            raise utils.handle_dynamo_error(err, "Failed to update user")
