import boto3
from mypy_boto3_dynamodb import DynamoDBServiceResource, DynamoDBClient

session = boto3.Session()

# type alias to dynamodb client
DynamoDBResource = DynamoDBServiceResource
_ddb_client: DynamoDBClient = session.client("dynamodb")
_ddb_resource: DynamoDBResource = session.resource("dynamodb")


def create_ddb_client() -> DynamoDBClient:
    return _ddb_client


def create_ddb_resource() -> DynamoDBResource:
    return _ddb_resource
