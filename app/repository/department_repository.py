import uuid
import time

from pydantic import ValidationError
from app.models.department import Department
from app.repository import DynamoDBResource, utils
from boto3.dynamodb.conditions import Key


class DepartmentRepository:
    def __init__(self,
                 ddb_resource: DynamoDBResource,
                 table_name: str):
        self._table = ddb_resource.Table(table_name)
        self._table_name = table_name
        self._pk = "DEPARTMENT"
        self._sk_prefix = "DETAILS#"

    def _get_department_primary_key(self, dep_id: str) -> dict:
        return {
            "PK": self._pk,
            "SK": f"{self._sk_prefix}{dep_id}",
        }

    def _parse_department_item(self, item: dict) -> Department:
        try:
            return Department.model_validate(item, by_alias=True)
        except ValidationError as err:
            print("Error constructing the model from fetched data: ", err)
            raise err

    def save(self, department: Department) -> None:
        if not department.id:
            department.id = str(uuid.uuid4())
        if not department.created_at:
            department.created_at = int(time.time_ns()//1e6)
            department.updated_at = department.created_at
        primary_key = self._get_department_primary_key(department.id)
        self._table.put_item(Item={
            **primary_key,
            **department.model_dump(by_alias=True)
        })

    def get(self, department_id: str) -> Department | None:
        primary_key = self._get_department_primary_key(department_id)
        response = self._table.get_item(Key=primary_key)
        if not response or "Item" not in response:
            return None
        return self._parse_department_item(response["Item"])

    def get_all(self) -> list[Department]:
        response = self._table.query(
            KeyConditionExpression=Key("PK").eq(
                self._pk) & Key("SK").begins_with(self._sk_prefix)
        )
        if not response or "Items" not in response:
            return []
        departments = [
            self._parse_department_item(item)
            for item in response["Items"]
        ]
        return departments

    def update(self, department: Department) -> None:
        existing_department = self.get(department.id)
        if not existing_department:
            raise Exception(f"Department with department_id: {
                            department.id} not found")

        department.updated_at = int(time.time_ns() // 1e6)
        exclude_fields = {'id', 'created_at'}
        to_update = department.model_dump(
            by_alias=True, exclude=exclude_fields)
        update_expr, expr_names, expr_values = utils.build_update_expression(
            to_update)

        primary_key = self._get_department_primary_key(department.id)
        self._table.update_item(
            Key=primary_key,
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
        )
