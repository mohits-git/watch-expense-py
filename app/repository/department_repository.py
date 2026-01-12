import asyncio
import uuid
import time

from botocore.exceptions import ClientError
from mypy_boto3_dynamodb.type_defs import QueryInputTableQueryTypeDef, TransactWriteItemTypeDef
from pydantic import ValidationError
from mypy_boto3_dynamodb.service_resource import Table
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.models.department import Department
from app.repository import utils
from boto3.dynamodb.conditions import Key


class DepartmentRepository:
    def __init__(self, ddb_table: Table, table_name: str):
        self._table = ddb_table
        self._table_name = table_name
        self._pk_prefix = "DEPARTMENT"
        self._sk_prefix = "DETAILS"

    def _get_primary_key(self, *,
                         department_id: str | None = None,
                         created_at: int | None = None) -> dict:
        pk_suffix = ""
        sk_suffix = ""
        if created_at:
            sk_suffix = f"#{created_at}#{department_id or ""}"
        elif department_id:
            pk_suffix = f"#{department_id}"
        return {
            "PK": f"{self._pk_prefix}{pk_suffix}",
            "SK": f"{self._sk_prefix}{sk_suffix}",
        }

    def _parse_department_item(self, item: dict) -> Department:
        try:
            return Department.model_validate(item, by_alias=True)
        except ValidationError as err:
            raise AppException(
                AppErr.INTERNAL,
                "Failed to parse department from database",
                cause=err,
            )

    async def save(self, department: Department) -> None:
        if not department.id:
            department.id = str(uuid.uuid4())
        if not department.created_at:
            department.created_at = int(time.time_ns() // 1e6)
            department.updated_at = department.created_at

        primary_key = self._get_primary_key(department_id=department.id)
        fetch_all_primary_key = self._get_primary_key(
            created_at=department.created_at,
            department_id=department.id)
        department_data = department.model_dump(by_alias=True)

        transact_items: list[TransactWriteItemTypeDef] = [
            {
                "Put": {
                    "TableName": self._table_name,
                    "Item": {
                        **primary_key,
                        **department_data,
                    },
                    "ConditionExpression": "attribute_not_exists(PK)",
                }
            },
            {
                "Put": {
                    "TableName": self._table_name,
                    "Item": {
                        **fetch_all_primary_key,
                        **department_data,
                    },
                    "ConditionExpression": "attribute_not_exists(SK)"
                }
            },
        ]

        try:
            await asyncio.to_thread(lambda: self._table.meta.client.transact_write_items(
                TransactItems=transact_items))
        except ClientError as err:
            if utils.is_conditional_check_failure(err):
                raise AppException(AppErr.DEPARTMENT_ALREADY_EXISTS, cause=err)
            raise utils.handle_dynamo_error(err, "Failed to save department")

    async def get(self, department_id: str) -> Department | None:
        try:
            primary_key = self._get_primary_key(department_id=department_id)
            response = await asyncio.to_thread(
                lambda: self._table.get_item(Key=primary_key))
            if not response or "Item" not in response:
                return None
            return self._parse_department_item(response["Item"])
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to get department")

    async def get_all(self) -> list[Department]:
        try:
            fetch_all_primary_key = self._get_primary_key()
            query_input: QueryInputTableQueryTypeDef = {
                "KeyConditionExpression": Key("PK").eq(
                    fetch_all_primary_key["PK"])
            }
            items = await utils.query_items(self._table, query_input)
            departments = [self._parse_department_item(item) for item in items]
            return departments
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to fetch departments")

    async def update(self, department: Department) -> None:
        existing_department = await self.get(department.id)
        if not existing_department:
            raise AppException(
                AppErr.NOT_FOUND,
                "Department not found")

        department.updated_at = int(time.time_ns() // 1e6)
        exclude_fields = {"id", "created_at"}
        to_update = department.model_dump(
            by_alias=True, exclude=exclude_fields)
        update_expr, expr_names, expr_values = utils.build_update_expression(
            to_update)

        primary_key = self._get_primary_key(department_id=department.id)
        fetch_all_primary_key = self._get_primary_key(
            created_at=existing_department.created_at,
            department_id=department.id)

        transact_items: list[TransactWriteItemTypeDef] = [
            {
                "Update": {
                    "TableName": self._table_name,
                    "Key": primary_key,
                    "UpdateExpression": update_expr,
                    "ExpressionAttributeNames": expr_names,
                    "ExpressionAttributeValues": expr_values,
                }
            },
            {
                "Update": {
                    "TableName": self._table_name,
                    "Key": fetch_all_primary_key,
                    "UpdateExpression": update_expr,
                    "ExpressionAttributeNames": expr_names,
                    "ExpressionAttributeValues": expr_values,
                }
            },
        ]

        try:
            await asyncio.to_thread(lambda: self._table.meta.client.transact_write_items(
                TransactItems=transact_items))
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to update department")
