import boto3
from mypy_boto3_dynamodb import DynamoDBServiceResource, DynamoDBClient

session = boto3.Session(
    region_name="us-east-1",
    aws_access_key_id="AKIA4WVWY5SE7S2U2Q5T",
    aws_secret_access_key="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",
)

# type alias to dynamodb client
DynamoDBResource = DynamoDBServiceResource
_ddb_client: DynamoDBClient = session.client("dynamodb")
_ddb_resource: DynamoDBResource = session.resource("dynamodb")


def create_ddb_client() -> DynamoDBClient:
    return _ddb_client


def create_ddb_resource() -> DynamoDBResource:
    return _ddb_resource
