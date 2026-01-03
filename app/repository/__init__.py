import boto3
from mypy_boto3_dynamodb import DynamoDBServiceResource

# type alias to dynamodb client
DynamoDBClient = DynamoDBServiceResource


def create_ddb_client() -> DynamoDBClient:
    dynamodb = DynamoDBClient(boto3.resource("dynamodb"))
    return dynamodb
