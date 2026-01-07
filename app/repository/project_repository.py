import uuid
import time

from botocore.utils import ClientError
from pydantic import ValidationError
from types_aiobotocore_dynamodb.service_resource import Table
from types_aiobotocore_dynamodb.type_defs import TransactWriteItemTypeDef
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
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
            raise AppException(
                AppErr.INTERNAL,
                "Failed to parse user from database",
                cause=err,
            )

    async def _get_dep_id_by_project_id(self, project_id: str) -> str | None:
        try:
            primary_key = self._get_project_lookup_primary_key(project_id)
            response = await self._table.get_item(
                Key=primary_key)
            if not response or "Item" not in response:
                return None
            return str(response["Item"]["DepartmentID"])
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to get project data")

    async def save(self, project: Project) -> None:
        if not project.id:
            project.id = str(uuid.uuid4())
        if not project.created_at:
            project.created_at = int(time.time_ns()//1e6)
            project.updated_at = project.created_at
        primary_key = self._get_project_primary_key(
            project.department_id, project.id)
        lookup_pk = self._get_project_lookup_primary_key(project.id)

        transact_items: list[TransactWriteItemTypeDef] = [
            {
                "Put": {
                    "TableName": self._table_name,
                    "Item": {
                        **primary_key,
                        **project.model_dump(by_alias=True),
                    },
                    "ConditionExpression": "attribute_not_exists(PK) AND attribute_not_exists(SK)"
                }
            },
            {
                "Put": {
                    "TableName": self._table_name,
                    "Item": {
                        **lookup_pk,
                        "DepartmentID": project.department_id,
                    },
                    "ConditionExpression": "attribute_not_exists(PK) AND attribute_not_exists(SK)"
                }
            }
        ]
        try:
            await self._table.meta.client.transact_write_items(TransactItems=transact_items)
        except self._table.meta.client.exceptions.TransactionCanceledException as err:
            reasons = err.response.get("CancellationReasons", [])
            codes = {r.get("Code") for r in reasons}
            if "ConditionalCheckFailed" in codes:
                raise AppException(
                    AppErr.PROJECT_ALREADY_EXISTS,
                    "Project already exists",
                    cause=err,
                )
            raise utils.handle_dynamo_error(err, "Failed to save project")
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to save project")

    async def get(self, project_id: str) -> Project | None:
        try:
            department_id = await self._get_dep_id_by_project_id(project_id)
            if not department_id:
                return None
            primary_key = self._get_project_primary_key(department_id, project_id)
            response = await self._table.get_item(Key=primary_key)
            if not response or "Item" not in response:
                return None
            return self._parse_project_item(response["Item"])
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to get project")

    async def get_all(self) -> list[Project]:
        try:
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
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to fetch projects")

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
            try:
                await self._table.update_item(
                    Key=primary_key,
                    UpdateExpression=update_expr,
                    ExpressionAttributeNames=expr_names,
                    ExpressionAttributeValues=expr_values,
                )
            except ClientError as err:
                raise utils.handle_dynamo_error(
                    err, "Failed to update project")
            return

        primary_key = self._get_project_primary_key(prev_dep_id, project.id)
        new_primary_key = self._get_project_primary_key(
            project.department_id, project.id)
        lookup_pk = self._get_project_lookup_primary_key(project.id)
        to_update = {"DepartmentID": project.department_id}
        update_expr, expr_names, expr_values = utils.build_update_expression(
            to_update)
        project.created_at = existing_project.created_at
        transact_items: list[TransactWriteItemTypeDef] = [
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
                    "ConditionExpression": "attribute_exists(PK) AND attribute_exists(SK)",
                }
            },
            {
                "Put": {
                    "TableName": self._table_name,
                    "Item": {
                        **new_primary_key,
                        **project.model_dump(by_alias=True)
                    },
                    "ConditionExpression": "attribute_not_exists(PK) AND attribute_not_exists(SK)"
                }
            }
        ]

        try:
            await self._table.meta.client.transact_write_items(TransactItems=transact_items)
        except self._table.meta.client.exceptions.TransactionCanceledException as err:
            reasons = err.response.get("CancellationReasons", [])
            codes = {r.get("Code") for r in reasons}
            if "ConditionalCheckFailed" in codes:
                raise AppException(
                    AppErr.NOT_FOUND,
                    "User not found",
                    cause=err,
                )
            raise utils.handle_dynamo_error(err, "Failed to update project")
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to update project")
