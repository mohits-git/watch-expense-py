import uuid
import time
from app.models.user import User
from app.repository import DynamoDBClient


class UserRepository():
    def __init__(self, ddb_sdk_client: DynamoDBClient, table_name: str):
        self._table = ddb_sdk_client.Table(table_name)

    def _get_user_primary_key(self, user_id: str) -> dict:
        return {
            "PK": "USER",
            "SK": f"PROFILE#{user_id}",
        }

    def save(self, user: User) -> None:
        if not user.id:
            user.id = str(uuid.uuid4())
        if not user.created_at:
            user.created_at = int(time.time() * 1000)
            user.updated_at = user.created_at
        primary_key = self._get_user_primary_key(user.id)
        res = self._table.put_item(Item={
            **primary_key,
            **user.model_dump(by_alias=True),
        })
        print("DynamoDB put_item response:", res)
