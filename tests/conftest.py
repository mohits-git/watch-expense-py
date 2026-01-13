import boto3
import pytest


@pytest.fixture(scope="session")
def boto3_session():
    return boto3.Session()
