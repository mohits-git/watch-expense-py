import asyncio
import uuid
import time

from botocore.utils import ClientError
from pydantic import ValidationError
from mypy_boto3_dynamodb.service_resource import Table
from mypy_boto3_dynamodb.type_defs import QueryInputTableQueryTypeDef, TransactWriteItemTypeDef
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
        self._pk_prefix = "PROJECT"
        self._sk_prefix = "DETAILS"
        self._dep_pk_prefix = "DEPARTMENT"
        self._dep_proj_sk_prefix = "PROJECT"

    def _get_primary_key(self, *,
                         project_id: str | None = None,
                         created_at: int | None = None,
                         ) -> dict:
        pk_suffix = ""
        sk_suffix = ""
        if created_at:
            sk_suffix = f"#{created_at}#{project_id or ""}"
        elif project_id:
            pk_suffix = f"#{project_id}"
        return {
            "PK": f"{self._pk_prefix}{pk_suffix}",
            "SK": f"{self._sk_prefix}{sk_suffix}",
        }

    def _get_departments_project_pk(self,
                                    department_id: str,
                                    *,
                                    created_at: int | None = None,
                                    project_id: str | None = None) -> dict:
        sk_suffix = ""
        if created_at:
            sk_suffix = f"#{created_at}#{project_id or ""}"
        return {
            "PK": f"{self._dep_pk_prefix}#{department_id}",
            "SK": f"{self._dep_proj_sk_prefix}#{sk_suffix}"
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

    async def save(self, project: Project) -> None:
        if not project.id:
            project.id = str(uuid.uuid4())
        if not project.created_at:
            project.created_at = int(time.time_ns()//1e6)
            project.updated_at = project.created_at

        primary_key = self._get_primary_key(project_id=project.id)
        fetch_all_primary_key = self._get_primary_key(
            created_at=project.created_at,
            project_id=project.id)
        dep_projects_primary_key = self._get_departments_project_pk(
            project.department_id,
            created_at=project.created_at,
            project_id=project.id)
        project_data = project.model_dump(by_alias=True)

        transact_items: list[TransactWriteItemTypeDef] = [
            {
                "Put": {
                    "TableName": self._table_name,
                    "Item": {
                        **primary_key,
                        **project_data,
                    },
                    "ConditionExpression": "attribute_not_exists(PK)",
                }
            },
            {
                "Put": {
                    "TableName": self._table_name,
                    "Item": {
                        **fetch_all_primary_key,
                        **project_data,
                    },
                    "ConditionExpression": "attribute_not_exists(SK)"
                }
            },
            {
                "Put": {
                    "TableName": self._table_name,
                    "Item": {
                        **dep_projects_primary_key,
                        **project_data,
                    },
                    "ConditionExpression": "attribute_not_exists(SK)"
                }
            }
        ]
        try:
            await asyncio.to_thread(
                lambda: self._table.meta.client.transact_write_items(
                    TransactItems=transact_items))
        except ClientError as err:
            if utils.is_conditional_check_failure(err):
                raise AppException(AppErr.PROJECT_ALREADY_EXISTS, cause=err)
            raise utils.handle_dynamo_error(err, "Failed to save project")

    async def get(self, project_id: str) -> Project | None:
        try:
            primary_key = self._get_primary_key(
                project_id=project_id)
            response = await asyncio.to_thread(
                lambda: self._table.get_item(Key=primary_key))
            if not response or "Item" not in response:
                return None
            return self._parse_project_item(response["Item"])
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to get project")

    async def get_all(self) -> list[Project]:
        try:
            fetch_all_primary_key = self._get_primary_key()
            query_input: QueryInputTableQueryTypeDef = {
                "KeyConditionExpression": Key("PK").eq(fetch_all_primary_key["PK"])
            }
            items = await utils.query_items(self._table, query_input)
            projects = [
                self._parse_project_item(item)
                for item in items
            ]
            return projects
        except ClientError as err:
            raise utils.handle_dynamo_error(err, "Failed to fetch projects")

    async def update(self, project: Project) -> None:
        existing_project = await self.get(project.id)
        if existing_project is None:
            raise Exception(f"Project with project_id: {project.id} not found")

        prev_dep_id = existing_project.department_id

        project.created_at = existing_project.created_at
        project.updated_at = int(time.time_ns() // 1e6)

        exclude_fields = {'id', 'created_at'}
        to_update = project.model_dump(
            by_alias=True, exclude=exclude_fields)
        update_expr, expr_names, expr_values = utils.build_update_expression(
            to_update)
        primary_key = self._get_primary_key(project_id=project.id)
        fetch_all_primary_key = self._get_primary_key(
            project_id=project.id,
            created_at=existing_project.created_at)
        dep_projects_pk = self._get_departments_project_pk(
            project_id=project.id,
            created_at=existing_project.created_at,
            department_id=prev_dep_id)

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

        if prev_dep_id != project.department_id:
            new_dep_projects_pk = self._get_departments_project_pk(
                project_id=project.id,
                created_at=existing_project.created_at,
                department_id=project.department_id,
            )
            transact_items.append({
                "Delete": {
                    "TableName": self._table_name,
                    "Key": dep_projects_pk,
                }
            })
            transact_items.append({
                "Put": {
                    "TableName": self._table_name,
                    "Item": {
                        **new_dep_projects_pk,
                        **project.model_dump(by_alias=True)
                    }
                }
            })
        else:
            transact_items.append({
                "Update": {
                    "TableName": self._table_name,
                    "Key": dep_projects_pk,
                    "UpdateExpression": update_expr,
                    "ExpressionAttributeNames": expr_names,
                    "ExpressionAttributeValues": expr_values,
                    "ConditionExpression": "attribute_exists(PK) AND attribute_exists(SK)",
                }
            })

        try:
            await asyncio.to_thread(
                lambda: self._table.meta.client.transact_write_items(
                    TransactItems=transact_items))
        except ClientError as err:
            if utils.is_conditional_check_failure(err):
                raise AppException(
                    AppErr.NOT_FOUND,
                    "User not found",
                    cause=err,
                )
            raise utils.handle_dynamo_error(err, "Failed to update project")
