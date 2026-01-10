import asyncio
from decimal import Decimal
import uuid
import time

from botocore.exceptions import ClientError
from pydantic import ValidationError
from mypy_boto3_dynamodb.service_resource import Table
from mypy_boto3_dynamodb.type_defs import QueryInputTableQueryTypeDef, TransactWriteItemTypeDef
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.models.expense import Expense, ExpensesFilterOptions, RequestStatus
from boto3.dynamodb.conditions import Attr, Key
from app.repository import utils


class ExpenseRepository:
    def __init__(self, ddb_table: Table, table_name: str):
        self._table = ddb_table
        self._table_name = table_name
        self._pk = "EXPENSE"
        self._sk_prefix = "DETAILS#"
        self._lookup_sk_prefix = "USER#"

    def _get_expense_primary_key(self, user_id: str, expense_id: str) -> dict:
        return {
            "PK": self._pk,
            "SK": f"{self._sk_prefix}{user_id}#{expense_id}",
        }

    def _get_lookup_primary_key(self, expense_id: str) -> dict:
        return {
            "PK": self._pk,
            "SK": f"{self._lookup_sk_prefix}{expense_id}",
        }

    async def _get_user_id_by_expense_id(self, expense_id: str) -> str | None:
        try:
            lookup_primary_key = self._get_lookup_primary_key(expense_id)
            response = await asyncio.to_thread(lambda: self._table.get_item(Key=lookup_primary_key))
            if not response or "Item" not in response:
                return None
            return str(response["Item"]["UserID"])
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to get expense data")

    def _parse_expense_item(self, item: dict) -> Expense:
        try:
            return Expense.model_validate(item, by_alias=True)
        except ValidationError as err:
            raise AppException(
                AppErr.INTERNAL,
                "Failed to parse expense from database",
                cause=err,
            )

    async def save(self, expense: Expense, reconciled_advance: str | None = None) -> None:
        if not expense.id:
            expense.id = str(uuid.uuid4())
        if not expense.created_at:
            expense.created_at = int(time.time_ns() // 1e6)
            expense.updated_at = expense.created_at
        primary_key = self._get_expense_primary_key(
            expense.user_id, expense.id)
        lookup_pk = self._get_lookup_primary_key(expense.id)
        transact_items: list[TransactWriteItemTypeDef] = [
            {
                "Put": {
                    "TableName": self._table_name,
                    "Item": {
                        **primary_key,
                        **expense.model_dump(by_alias=True),
                    },
                    "ConditionExpression": "attribute_not_exists(PK) AND attribute_not_exists(SK)",
                }
            },
            {
                "Put": {
                    "TableName": self._table_name,
                    "Item": {
                        **lookup_pk,
                        "UserID": expense.user_id,
                    },
                    "ConditionExpression": "attribute_not_exists(PK) AND attribute_not_exists(SK)",
                }
            },
        ]
        if reconciled_advance:
            advance_primary_key = {
                "PK": "ADVANCE",
                "SK": f"DETAILS#{expense.user_id}#{reconciled_advance}"
            }
            transact_items.append({
                "Update": {
                    "TableName": self._table_name,
                    "Key": advance_primary_key,
                    "UpdateExpression": "SET #ReconciledExpenseID = :expenseId",
                    "ExpressionAttributeNames": {
                        "#ReconciledExpenseID": "ReconciledExpenseID",
                    },
                    "ExpressionAttributeValues": {
                        ":expenseId": expense.id,
                    },
                }
            })
        try:
            await asyncio.to_thread(lambda: self._table.meta.client.transact_write_items(
                TransactItems=transact_items))
        except ClientError as err:
            if utils.is_conditional_check_failure(err):
                raise AppException(AppErr.EXPENSE_ALREADY_EXISTS, cause=err)
            raise utils.handle_dynamo_error(err, "Failed to save expense")

    async def get(self, expense_id: str) -> Expense | None:
        try:
            user_id = await self._get_user_id_by_expense_id(expense_id)
            if not user_id:
                return None
            primary_key = self._get_expense_primary_key(user_id, expense_id)
            response = await asyncio.to_thread(lambda: self._table.get_item(Key=primary_key))
            if not response or "Item" not in response:
                return None
            return self._parse_expense_item(response["Item"])
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to get expense")

    async def get_all(
        self,
        filterOptions: ExpensesFilterOptions,
    ) -> tuple[list[Expense], int]:
        try:
            query_input: QueryInputTableQueryTypeDef | None = {
                "KeyConditionExpression": Key("PK").eq(self._pk)
                & Key("SK").begins_with(f"{self._sk_prefix}{filterOptions.user_id or ''}"),
            }

            if filterOptions.status is not None:
                query_input["FilterExpression"] = Attr(
                    "Status").eq(filterOptions.status)

            # Total count
            query_input["Select"] = "COUNT"
            count_response = await asyncio.to_thread(lambda: self._table.query(**query_input))
            if "Count" not in count_response:
                return ([], 0)
            total_records = int(count_response["Count"])

            # pagination / fast pagination
            query_input = await utils.offset_query(
                self._table, query_input, filterOptions.page - 1, filterOptions.limit
            )
            if query_input is None:
                return ([], 0)

            # query expenses
            query_input["Select"] = "ALL_ATTRIBUTES"
            query_input["Limit"] = filterOptions.limit
            items = await utils.query_items(self._table, query_input, filterOptions.limit)
            expenses = [self._parse_expense_item(item) for item in items]
            return (expenses, total_records)
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to fetch expenses")

    async def update(self, expense: Expense):
        existing_expense = await self.get(expense.id)
        if not existing_expense:
            raise AppException(
                AppErr.NOT_FOUND,
                "Expense not found",
            )

        expense.updated_at = int(time.time_ns() // 1e6)
        exclude_fields = {"id", "created_at", "user_id"}
        to_update = expense.model_dump(by_alias=True, exclude=exclude_fields)
        update_expr, expr_names, expr_values = utils.build_update_expression(
            to_update)

        primary_key = self._get_expense_primary_key(
            expense.user_id, expense.id)
        try:
            await asyncio.to_thread(lambda: self._table.update_item(
                Key=primary_key,
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues=expr_values,
                ConditionExpression="attribute_exists(PK) AND attribute_exists(SK)",
            ))
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to update expense")

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

            items = await utils.query_items(self._table, queryInput)

            expenses_sum = 0.0
            for item in items:
                amount = item["Amount"]
                if amount and isinstance(amount, Decimal):
                    expenses_sum += float(amount)
            return expenses_sum
        except ClientError as err:
            raise utils.handle_dynamo_error(
                err, "Failed to calculate expenses sum")
