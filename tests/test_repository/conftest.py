import pytest


@pytest.fixture(scope="session")
def table_name():
    return "test-watch-expense-table"


@pytest.fixture(scope="session")
def ddb_table(boto3_session, table_name):
    ddb = boto3_session.resource("dynamodb", region_name="ap-south-1")
    table = ddb.create_table(
        TableName=table_name,
        KeySchema=[
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"},
        ],
        ProvisionedThroughput={
            "ReadCapacityUnits": 5,
            "WriteCapacityUnits": 5,
        },
    )
    table.wait_until_exists()
    yield table
    table.delete()
    table.wait_until_not_exists()
