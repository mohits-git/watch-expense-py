from decimal import Decimal
import uuid
import time

from mypy_boto3_dynamodb.type_defs import QueryInputTableQueryTypeDef
from pydantic import ValidationError
from app.models.expense import Expense, ExpensesFilterOptions, RequestStatus
from app.repository import DynamoDBResource
from boto3.dynamodb.conditions import Attr, Key
from app.repository import utils


class ExpenseRepository():
    def __init__(self,
                 ddb_resource: DynamoDBResource,
                 table_name: str):
        self._table = ddb_resource.Table(table_name)
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

    def _get_user_id_by_expense_id(self, expense_id: str) -> str | None:
        lookup_primary_key = self._get_lookup_primary_key(expense_id)
        response = self._table.get_item(
            Key=lookup_primary_key)
        if not response or "Item" not in response:
            return None
        return str(response["Item"]["UserID"])

    def _parse_expense_item(self, item: dict) -> Expense:
        try:
            return Expense.model_validate(item, by_alias=True)
        except ValidationError as err:
            print("Error constructing the model from fetched data: ", err)
            raise err

    def save(self, expense: Expense):
        if not expense.id:
            expense.id = str(uuid.uuid4())
        if not expense.created_at:
            expense.created_at = int(time.time_ns()//1e6)
            expense.updated_at = expense.created_at
        primary_key = self._get_expense_primary_key(
            expense.user_id, expense.id)
        lookup_pk = self._get_lookup_primary_key(expense.id)
        with self._table.batch_writer() as batch:
            batch.put_item(Item={
                **primary_key,
                **expense.model_dump(by_alias=True),
            })
            batch.put_item(Item={
                **lookup_pk,
                "UserID": expense.user_id,
            })

    def get(self, expense_id: str) -> Expense | None:
        user_id = self._get_user_id_by_expense_id(expense_id)
        if not user_id:
            return None
        primary_key = self._get_expense_primary_key(user_id, expense_id)
        response = self._table.get_item(Key=primary_key)
        if not response or "Item" not in response:
            return None
        return self._parse_expense_item(response["Item"])

    def get_all(self,
                filterOptions: ExpensesFilterOptions,
                ) -> tuple[list[Expense], int]:
        query_input: QueryInputTableQueryTypeDef | None = {
            "KeyConditionExpression": Key("PK").eq(self._pk) & Key(
                "SK").begins_with(f"{self._sk_prefix}{filterOptions.user_id}"),
        }

        if filterOptions.status is not None:
            query_input["FilterExpression"] = Attr(
                'Status').eq(filterOptions.status)

        # Total count
        query_input["Select"] = "COUNT"
        count_response = self._table.query(**query_input)
        if 'Count' not in count_response:
            return ([], 0)
        total_records = int(count_response['Count'])

        # pagination / fast pagination
        query_input = utils.offset_query(
            self._table,
            query_input,
            filterOptions.page,
            filterOptions.limit
        )
        if query_input is None:
            return ([], 0)

        # query expenses
        query_input["Select"] = 'ALL_ATTRIBUTES'
        query_input["Limit"] = filterOptions.limit
        response = self._table.query(**query_input)
        if not response or "Items" not in response:
            raise Exception("Unable to fetch expenses")
        expenses = [
            self._parse_expense_item(item)
            for item in response["Items"]
        ]
        return (expenses, total_records)

    def update(self, expense: Expense):
        existing_expense = self.get(expense.id)
        if not existing_expense:
            raise Exception(f"expense with expense_id: {
                            expense.id} not found")

        expense.updated_at = int(time.time_ns() // 1e6)
        exclude_fields = {'id', 'created_at', 'user_id'}
        to_update = expense.model_dump(
            by_alias=True, exclude=exclude_fields)
        update_expr, expr_names, expr_values = utils.build_update_expression(
            to_update)

        primary_key = self._get_expense_primary_key(
            expense.user_id, expense.id)
        self._table.update_item(
            Key=primary_key,
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
        )

    def get_expense_sum(self,
                        user_id: str = "",
                        status: RequestStatus | None = None) -> float:
        queryInput: QueryInputTableQueryTypeDef = {
            "KeyConditionExpression": Key("PK").eq(self._pk) & Key(
                "SK").begins_with(f"{self._sk_prefix}{user_id}"),
            "ProjectionExpression": "Amount",
        }

        if status is not None:
            queryInput["FilterExpression"] = Attr('Status').eq(status)

        response = self._table.query(**queryInput)
        if not response or "Items" not in response:
            raise Exception("Unable to fetch expenses")

        expenses_sum = 0.0
        for item in response['Items']:
            amount = item["Amount"]
            if amount and isinstance(amount, Decimal):
                expenses_sum += float(amount)
        return expenses_sum
