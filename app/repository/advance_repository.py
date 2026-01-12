import asyncio
from decimal import Decimal
import uuid
import time

from botocore.exceptions import ClientError
from pydantic import ValidationError
from mypy_boto3_dynamodb.service_resource import Table
from mypy_boto3_dynamodb.type_defs import (
    QueryInputTableQueryTypeDef,
    TransactWriteItemTypeDef
)
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.models.advance import Advance, AdvancesFilterOptions, RequestStatus
from boto3.dynamodb.conditions import Attr, Key
from app.repository import utils


class AdvanceRepository:
    def __init__(self, ddb_table: Table, table_name: str):
        self._table = ddb_table
        self._table_name = table_name
        self._pk_prefix = "ADVANCE"
        self._sk_prefix = "DETAILS"
        self._users_advance_pk_prefix = "USER"
        self._users_advance_sk_prefix = "ADVANCE"

    def _get_primary_key(self, *,
                         advance_id: str | None = None,
                         created_at: int | None = None) -> dict:
        pk_suffix = ""
        sk_suffix = ""
        if created_at:
            sk_suffix = f"#{created_at}#{advance_id or ""}"
        elif advance_id:
            pk_suffix = f"#{advance_id}"
        return {
            "PK": f"{self._pk_prefix}{pk_suffix}",
            "SK": f"{self._sk_prefix}{sk_suffix}"
        }

    def _get_users_advances_pk(self,
                               user_id: str,
                               *,
                               created_at: int | None = None,
                               advance_id: str | None = None,
                               ) -> dict:
        sk_suffix = ""
        if created_at:
            sk_suffix = f"#{created_at}#{advance_id or ''}"
        return {
            "PK": f"{self._users_advance_pk_prefix}#{user_id}",
            "SK": f"{self._users_advance_sk_prefix}{sk_suffix}"
        }

    def _parse_advance_item(self, item: dict) -> Advance:
        try:
            return Advance.model_validate(item, by_alias=True)
        except ValidationError as err:
            raise AppException(
                AppErr.INTERNAL,
                "Failed to parse advance from database",
                cause=err,
            )

    async def save(self, advance: Advance) -> None:
        if not advance.id:
            advance.id = str(uuid.uuid4())
        if not advance.created_at:
            advance.created_at = int(time.time_ns() // 1e6)
            advance.updated_at = advance.created_at

        primary_key = self._get_primary_key(
            advance_id=advance.id)
        fetch_all_primary_key = self._get_primary_key(
            advance_id=advance.id, created_at=advance.created_at)
        users_advances_pk = self._get_users_advances_pk(
            advance.user_id,
            created_at=advance.created_at,
            advance_id=advance.id)
        advance_data = advance.model_dump(by_alias=True)

        transact_items: list[TransactWriteItemTypeDef] = [
            {
                "Put": {
                    "TableName": self._table_name,
                    "Item": {
                        **primary_key,
                        **advance_data,
                    },
                    "ConditionExpression": "attribute_not_exists(PK)",
                }
            },
            {
                "Put": {
                    "TableName": self._table_name,
                    "Item": {
                        **fetch_all_primary_key,
                        **advance_data,
                    },
                    "ConditionExpression": "attribute_not_exists(PK)",
                }
            },
            {
                "Put": {
                    "TableName": self._table_name,
                    "Item": {
                        **users_advances_pk,
                        **advance_data,
                    },
                    "ConditionExpression": "attribute_not_exists(PK)",
                }
            },
        ]
        try:
            await asyncio.to_thread(lambda: self._table.meta.client.transact_write_items(
                TransactItems=transact_items))
        except ClientError as err:
            if utils.is_conditional_check_failure(err):
                raise AppException(AppErr.ADVANCE_ALREADY_EXISTS, cause=err)
            raise utils.handle_dynamo_error(err, "Failed to save advance")

    async def get(self, advance_id: str) -> Advance | None:
        try:
            primary_key = self._get_primary_key(advance_id=advance_id)
            response = await asyncio.to_thread(
                lambda: self._table.get_item(Key=primary_key))
            if not response or "Item" not in response:
                return None
            return self._parse_advance_item(response["Item"])
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to get advance")

    async def get_all(
        self,
        filterOptions: AdvancesFilterOptions,
    ) -> tuple[list[Advance], int]:
        try:
            # key query
            primary_key: dict = {}
            if filterOptions.user_id:
                primary_key = self._get_users_advances_pk(
                    user_id=filterOptions.user_id,
                )
            else:
                primary_key = self._get_primary_key()

            query_input: QueryInputTableQueryTypeDef = {
                "KeyConditionExpression": Key("PK").eq(primary_key["PK"])
                & Key("SK").begins_with(primary_key["SK"]),
            }

            # filter
            if filterOptions.status is not None:
                query_input["FilterExpression"] = Attr(
                    "Status").eq(filterOptions.status)

            # Total count
            query_input["Select"] = "COUNT"
            count_response = await asyncio.to_thread(lambda: self._table.query(**query_input))
            if "Count" not in count_response:
                return ([], 0)
            total_records = int(count_response["Count"])

            # pagination / fast cursor
            next_query_input = await utils.offset_query(
                self._table, query_input, filterOptions.page - 1, filterOptions.limit)
            if next_query_input is None:
                return ([], 0)
            query_input = next_query_input

            # query advances
            query_input["Select"] = "ALL_ATTRIBUTES"
            query_input["Limit"] = filterOptions.limit
            items = await utils.query_items(self._table, query_input, filterOptions.limit)
            advances = [self._parse_advance_item(
                item) for item in items]
            return (advances, total_records)
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to fetch advances")

    async def update(self, advance: Advance):
        existing_advance = await self.get(advance.id)
        if not existing_advance:
            raise AppException(
                AppErr.NOT_FOUND,
                "Advance not found")

        advance.updated_at = int(time.time_ns() // 1e6)
        exclude_fields = {"id", "created_at"}
        to_update = advance.model_dump(by_alias=True, exclude=exclude_fields)
        update_expr, expr_names, expr_values = utils.build_update_expression(
            to_update)

        primary_key = self._get_primary_key(
            advance_id=advance.id)
        fetch_all_primary_key = self._get_primary_key(
            created_at=existing_advance.created_at,
            advance_id=advance.id)
        users_advances_pk = self._get_users_advances_pk(
            existing_advance.user_id,
            created_at=existing_advance.created_at,
            advance_id=advance.id)

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
            },
            {
                "Update": {
                    "TableName": self._table_name,
                    "Key": users_advances_pk,
                    "UpdateExpression": update_expr,
                    "ExpressionAttributeNames": expr_names,
                    "ExpressionAttributeValues": expr_values,
                    "ConditionExpression": "attribute_exists(PK) AND attribute_exists(SK)",
                }
            },
        ]

        try:
            await asyncio.to_thread(lambda: self._table.meta.client.transact_write_items(
                TransactItems=transact_items))
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to update advance")

    async def get_sum(
        self, user_id: str = "", status: RequestStatus | None = None
    ) -> float:
        try:
            # key query
            primary_key: dict = {}
            if user_id:
                primary_key = self._get_users_advances_pk(user_id=user_id)
            else:
                primary_key = self._get_primary_key()

            query_input: QueryInputTableQueryTypeDef = {
                "KeyConditionExpression": Key("PK").eq(primary_key["PK"])
                & Key("SK").begins_with(primary_key["SK"]),
                "ProjectionExpression": "Amount",
            }

            if status is not None:
                query_input["FilterExpression"] = Attr("Status").eq(status)

            items = await utils.query_items(self._table, query_input)

            advances_sum = 0.0
            for item in items:
                amount = item["Amount"]
                if amount and isinstance(amount, Decimal):
                    advances_sum += float(amount)
            return advances_sum
        except ClientError as err:
            raise utils.handle_dynamo_error(
                err, "Failed to calculate advances sum")

    async def get_reconciled_sum(self, user_id: str) -> float:
        try:
            # key query
            primary_key: dict = {}
            if user_id:
                primary_key = self._get_users_advances_pk(user_id=user_id)
            else:
                primary_key = self._get_primary_key()

            query_input: QueryInputTableQueryTypeDef = {
                "KeyConditionExpression": Key("PK").eq(primary_key["PK"])
                & Key("SK").begins_with(primary_key["SK"]),
                "ProjectionExpression": "Amount",
                "FilterExpression": Attr("ReconciledExpenseID").exists()
                & Attr("ReconciledExpenseID").size().gt(0),
            }

            items = await utils.query_items(self._table, query_input)

            advances_sum = 0.0
            for item in items:
                amount = item["Amount"]
                if amount and isinstance(amount, Decimal):
                    advances_sum += float(amount)
            return advances_sum
        except ClientError as err:
            raise utils.handle_dynamo_error(
                err, "Failed to calculate reconciled advances sum")
