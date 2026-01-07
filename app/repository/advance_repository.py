from decimal import Decimal
import uuid
import time

from botocore.exceptions import ClientError
from pydantic import ValidationError
from types_aiobotocore_dynamodb.service_resource import Table
from types_aiobotocore_dynamodb.type_defs import QueryInputTableQueryTypeDef, TransactWriteItemTypeDef
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.models.advance import Advance, AdvancesFilterOptions, RequestStatus
from boto3.dynamodb.conditions import Attr, Key
from app.repository import utils


class AdvanceRepository:
    def __init__(self, ddb_table: Table, table_name: str):
        self._table = ddb_table
        self._table_name = table_name
        self._pk = "ADVANCE"
        self._sk_prefix = "DETAILS#"
        self._lookup_sk_prefix = "USER#"

    def _get_advance_primary_key(self, user_id: str, advance_id: str) -> dict:
        return {
            "PK": self._pk,
            "SK": f"{self._sk_prefix}{user_id}#{advance_id}",
        }

    def _get_lookup_primary_key(self, advance_id: str) -> dict:
        return {
            "PK": self._pk,
            "SK": f"{self._lookup_sk_prefix}{advance_id}",
        }

    async def _get_user_id_by_advance_id(self, advance_id: str) -> str | None:
        try:
            lookup_primary_key = self._get_lookup_primary_key(advance_id)
            response = await self._table.get_item(Key=lookup_primary_key)
            if not response or "Item" not in response:
                return None
            return str(response["Item"]["UserID"])
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to get advance data")

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
        primary_key = self._get_advance_primary_key(advance.user_id, advance.id)
        lookup_pk = self._get_lookup_primary_key(advance.id)

        transact_items: list[TransactWriteItemTypeDef] = [
            {
                "Put": {
                    "TableName": self._table_name,
                    "Item": {
                        **primary_key,
                        **advance.model_dump(by_alias=True),
                    },
                    "ConditionExpression": "attribute_not_exists(PK) AND attribute_not_exists(SK)",
                }
            },
            {
                "Put": {
                    "TableName": self._table_name,
                    "Item": {
                        **lookup_pk,
                        "UserID": advance.user_id,
                    },
                    "ConditionExpression": "attribute_not_exists(PK) AND attribute_not_exists(SK)",
                }
            },
        ]
        try:
            await self._table.meta.client.transact_write_items(
                TransactItems=transact_items)
        except self._table.meta.client.exceptions.TransactionCanceledException as err:
            reasons = err.response.get("CancellationReasons", [])
            codes = {r.get("Code") for r in reasons}
            if "ConditionalCheckFailed" in codes:
                raise AppException(
                    AppErr.ADVANCE_ALREADY_EXISTS,
                    "Advance already exists",
                    cause=err,
                )
            raise utils.handle_dynamo_error(err, "Failed to save advance")
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to save advance")

    async def get(self, advance_id: str) -> Advance | None:
        try:
            user_id = await self._get_user_id_by_advance_id(advance_id)
            if not user_id:
                return None
            primary_key = self._get_advance_primary_key(user_id, advance_id)
            response = await self._table.get_item(Key=primary_key)
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
            query_input: QueryInputTableQueryTypeDef | None = {
                "KeyConditionExpression": Key("PK").eq(self._pk)
                & Key("SK").begins_with(f"{self._sk_prefix}{filterOptions.user_id}"),
            }

            if filterOptions.status is not None:
                query_input["FilterExpression"] = Attr("Status").eq(filterOptions.status)

            # Total count
            query_input["Select"] = "COUNT"
            count_response = await self._table.query(**query_input)
            if "Count" not in count_response:
                return ([], 0)
            total_records = int(count_response["Count"])

            # pagination / fast pagination
            query_input = await utils.offset_query(
                self._table, query_input, filterOptions.page, filterOptions.limit
            )
            if query_input is None:
                return ([], 0)

            # query advances
            query_input["Select"] = "ALL_ATTRIBUTES"
            query_input["Limit"] = filterOptions.limit
            response = await self._table.query(**query_input)
            if not response or "Items" not in response:
                return ([], 0)
            advances = [self._parse_advance_item(item) for item in response["Items"]]
            return (advances, total_records)
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to fetch advances")

    async def update(self, advance: Advance):
        existing_advance = await self.get(advance.id)
        if not existing_advance:
            raise AppException(
                AppErr.NOT_FOUND,
                f"advance with advance_id: {advance.id} not found",
            )

        advance.updated_at = int(time.time_ns() // 1e6)
        exclude_fields = {"id", "created_at"}
        to_update = advance.model_dump(by_alias=True, exclude=exclude_fields)
        update_expr, expr_names, expr_values = utils.build_update_expression(to_update)

        primary_key = self._get_advance_primary_key(advance.user_id, advance.id)
        try:
            await self._table.update_item(
                Key=primary_key,
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues=expr_values,
                ConditionExpression="attribute_exists(PK) AND attribute_exists(SK)",
            )
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to update advance")

    async def get_sum(
        self, user_id: str = "", status: RequestStatus | None = None
    ) -> float:
        try:
            queryInput: QueryInputTableQueryTypeDef = {
                "KeyConditionExpression": Key("PK").eq(self._pk)
                & Key("SK").begins_with(f"{self._sk_prefix}{user_id}"),
                "ProjectionExpression": "Amount",
            }

            if status is not None:
                queryInput["FilterExpression"] = Attr("Status").eq(status)

            response = await self._table.query(**queryInput)
            if not response or "Items" not in response:
                return 0.0

            advances_sum = 0.0
            for item in response["Items"]:
                amount = item["Amount"]
                if amount and isinstance(amount, Decimal):
                    advances_sum += float(amount)
            return advances_sum
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to calculate advances sum")

    async def get_reconciled_sum(self, user_id: str) -> float:
        try:
            queryInput: QueryInputTableQueryTypeDef = {
                "KeyConditionExpression": Key("PK").eq(self._pk)
                & Key("SK").begins_with(f"{self._sk_prefix}{user_id}"),
                "ProjectionExpression": "Amount",
                "FilterExpression": Attr("ReconciledExpenseID").exists()
                & Attr("ReconciledExpenseID").size().gt(0),
            }

            response = await self._table.query(**queryInput)
            if not response or "Items" not in response:
                return 0.0

            advances_sum = 0.0
            for item in response["Items"]:
                amount = item["Amount"]
                if amount and isinstance(amount, Decimal):
                    advances_sum += float(amount)
            return advances_sum
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to calculate reconciled advances sum")
