import uuid
import time

from mypy_boto3_dynamodb.type_defs import TransactWriteItemTypeDef
from pydantic import ValidationError
from app.models.user import User
from app.repository import DynamoDBClient, DynamoDBResource
from boto3.dynamodb.conditions import Key
from app.repository import utils


class UserRepository():
    def __init__(self,
                 ddb_client: DynamoDBClient,
                 ddb_resource: DynamoDBResource,
                 table_name: str):
        self._client = ddb_client
        self._table = ddb_resource.Table(table_name)
        self._table_name = table_name

    def _get_user_primary_key(self, user_id: str) -> dict:
        return {
            "PK": "USER",
            "SK": f"PROFILE#{user_id}",
        }

    def _get_lookup_primary_key(self, email: str) -> dict:
        return {
            "PK": "USER",
            "SK": f"EMAIL#{email}"
        }

    def _parse_user_item(self, item: dict) -> User:
        try:
            return User.model_validate(item, by_alias=True)
        except ValidationError as err:
            print("Error constructing the model from fetched data: ", err)
            raise err

    def _get_email_by_id(self, user_id) -> str | None:
        primary_key = self._get_user_primary_key(user_id)
        response = self._table.get_item(Key={
            **primary_key
        }, ProjectionExpression="Email")
        if not response or "Item" not in response:
            return None
        return str(response["Item"]["Email"])

    def save(self, user: User) -> None:
        if not user.id:
            user.id = str(uuid.uuid4())
        if not user.created_at:
            user.created_at = int(time.time_ns()//1e6)
            user.updated_at = user.created_at
        primary_key = self._get_user_primary_key(user.id)
        lookup_pk = self._get_lookup_primary_key(user.email)
        with self._table.batch_writer() as batch:
            batch.put_item(Item={
                **primary_key,
                **user.model_dump(by_alias=True),
            })
            batch.put_item(Item={
                **lookup_pk,
                "UserID": user.id,
            })

    def get(self, user_id: str) -> User | None:
        primary_key = self._get_user_primary_key(user_id)
        response = self._table.get_item(Key=primary_key)
        if not response or "Item" not in response:
            return None
        return self._parse_user_item(response["Item"])

    def get_by_email(self, email: str) -> User | None:
        lookup_pk = self._get_lookup_primary_key(email)
        response = self._table.get_item(Key=lookup_pk)
        if not response or "Item" not in response:
            return None
        user_id = str(response["Item"]["UserID"])
        return self.get(user_id)

    def get_all(self) -> list[User]:
        response = self._table.query(
            KeyConditionExpression=Key("PK").eq(
                "USER") & Key("SK").begins_with("PROFILE#"))
        if not response or "Items" not in response:
            return []
        users = [
            self._parse_user_item(item)
            for item in response["Items"]
        ]
        return users

    def delete(self, user_id: str) -> None:
        email = self._get_email_by_id(user_id)
        if not email:
            raise Exception(f"User with user_id: {user_id} not found")
        primary_key = self._get_user_primary_key(user_id)
        lookup_pk = self._get_lookup_primary_key(email)
        with self._table.batch_writer() as batch:
            batch.delete_item(
                Key={
                    **primary_key
                }
            )
            batch.delete_item(
                Key={
                    **lookup_pk
                }
            )

    def update(self, user: User) -> None:
        existing_email = self._get_email_by_id(user.id)
        if not existing_email:
            raise Exception(f"User with user_id: {user.id} not found")

        transaction_items: list[TransactWriteItemTypeDef] = []

        # build update expression
        user.updated_at = int(time.time_ns() // 1e6)
        exclude_fields = {'id', 'created_at'}
        if user.password == '' or not user.password:
            exclude_fields.add('password')
        to_update = user.model_dump(
            by_alias=True, exclude=exclude_fields)
        update_expr, expr_names, expr_values = utils.build_update_expression(
            to_update)

        primary_key = self._get_user_primary_key(user.id)
        transaction_items.append({
            "Update": {
                "TableName": self._table_name,
                "Key": utils.python_to_dynamo(primary_key),
                "UpdateExpression": update_expr,
                "ExpressionAttributeNames": expr_names,
                "ExpressionAttributeValues": utils.python_to_dynamo(expr_values),
            }
        })

        if user.email != existing_email:
            lookup_pk = self._get_lookup_primary_key(existing_email)
            transaction_items.append({
                "Delete": {
                    "TableName": self._table_name,
                    "Key": utils.python_to_dynamo(lookup_pk),
                }
            })
            new_lookup_pk = self._get_lookup_primary_key(user.email)
            transaction_items.append({
                "Put": {
                    "TableName": self._table_name,
                    "Item": utils.python_to_dynamo(python_object={
                        **new_lookup_pk,
                        "UserID": user.id
                    }),
                }
            })

        try:
            self._client.transact_write_items(
                TransactItems=transaction_items)
        except self._table.meta.client.exceptions.TransactionCanceledException as err:
            print("Transaction err: ", err)
            for i, reason in enumerate(err.response["CancellationReasons"]):
                print(f"Item {i} cancellation reason:", reason)
            raise err
