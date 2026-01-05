import uuid
import time

from pydantic import ValidationError
from types_aiobotocore_dynamodb.service_resource import Table
from types_aiobotocore_dynamodb.type_defs import TransactWriteItemTypeDef
from app.models.project import Project
from boto3.dynamodb.conditions import Key
from app.repository import utils


class ProjectRepository:
    def __init__(self,
                 ddb_table: Table,
                 table_name: str):
        self._table = ddb_table
        self._table_name = table_name
        self._pk = "PROJECT"
        self._sk_prefix = "DETAILS#"
        self._lookup_sk_prefix = "DEPARTMENT#"

    def _get_project_primary_key(self, dep_id: str, project_id: str) -> dict:
        return {
            "PK": self._pk,
            "SK": f"{self._sk_prefix}{dep_id}#{project_id}",
        }

    def _get_project_lookup_primary_key(self, project_id: str) -> dict:
        return {
            "PK": self._pk,
            "SK": f"{self._lookup_sk_prefix}{project_id}",
        }

    def _parse_project_item(self, item: dict) -> Project:
        try:
            return Project.model_validate(item, by_alias=True)
        except ValidationError as err:
            print("Error constructing the model from fetched data: ", err)
            raise err

    async def _get_dep_id_by_project_id(self, project_id: str) -> str | None:
        primary_key = self._get_project_lookup_primary_key(project_id)
        response = await self._table.get_item(
            Key=primary_key)
        if not response or "Item" not in response:
            return None
        return str(response["Item"]["DepartmentID"])

    async def save(self, project: Project) -> None:
        if not project.id:
            project.id = str(uuid.uuid4())
        if not project.created_at:
            project.created_at = int(time.time_ns()//1e6)
            project.updated_at = project.created_at
        primary_key = self._get_project_primary_key(
            project.department_id, project.id)
        lookup_pk = self._get_project_lookup_primary_key(project.id)
        async with self._table.batch_writer() as batch:
            await batch.put_item(Item={
                **primary_key,
                **project.model_dump(by_alias=True),
            })
            await batch.put_item(Item={
                **lookup_pk,
                "DepartmentID": project.department_id,
            })

    async def get(self, project_id: str) -> Project | None:
        department_id = await self._get_dep_id_by_project_id(project_id)
        if not department_id:
            return None
        primary_key = self._get_project_primary_key(department_id, project_id)
        response = await self._table.get_item(Key=primary_key)
        if not response or "Item" not in response:
            return None
        return self._parse_project_item(response["Item"])

    async def get_all(self) -> list[Project]:
        response = await self._table.query(
            KeyConditionExpression=Key("PK").eq(
                self._pk) & Key("SK").begins_with(self._sk_prefix)
        )
        if not response or "Items" not in response:
            raise Exception("Unable to fetch projects")
        projects = [
            self._parse_project_item(item)
            for item in response["Items"]
        ]
        return projects

    async def update(self, project: Project) -> None:
        existing_project = await self.get(project.id)
        if existing_project is None:
            raise Exception(f"Project with project_id: {project.id} not found")
        prev_dep_id = existing_project.department_id

        project.updated_at = int(time.time_ns() // 1e6)

        if prev_dep_id == project.department_id:
            # build update expr
            exclude_fields = {'id', 'created_at'}
            to_update = project.model_dump(
                by_alias=True, exclude=exclude_fields)
            update_expr, expr_names, expr_values = utils.build_update_expression(
                to_update)
            primary_key = self._get_project_primary_key(
                prev_dep_id, project.id)
            await self._table.update_item(
                Key=primary_key,
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues=expr_values,
            )
            return

        primary_key = self._get_project_primary_key(prev_dep_id, project.id)
        new_primary_key = self._get_project_primary_key(
            project.department_id, project.id)
        lookup_pk = self._get_project_lookup_primary_key(project.id)
        to_update = {"DepartmentID": project.department_id}
        update_expr, expr_names, expr_values = utils.build_update_expression(
            to_update)
        project.created_at = existing_project.created_at
        transaction_items: list[TransactWriteItemTypeDef] = [
            {
                "Delete": {
                    "TableName": self._table_name,
                    "Key": primary_key,
                }
            },
            {
                "Update": {
                    "TableName": self._table_name,
                    "Key": lookup_pk,
                    "UpdateExpression": update_expr,
                    "ExpressionAttributeNames": expr_names,
                    "ExpressionAttributeValues": expr_values,
                }
            },
            {
                "Put": {
                    "TableName": self._table_name,
                    "Item": {
                        **new_primary_key,
                        **project.model_dump(by_alias=True)
                    }
                }
            }
        ]

        await self._table.meta.client.transact_write_items(
            TransactItems=transaction_items)
