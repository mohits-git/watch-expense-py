import boto3
import pytest
import os
from moto import mock_aws


@pytest.fixture(scope="session")
def aws_credentials():
    os.environ['AWS_ACCESS_KEY_ID'] = 'test'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'
    os.environ['AWS_SECURITY_TOKEN'] = 'test'
    os.environ['AWS_SESSION_TOKEN'] = 'test'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


@pytest.fixture(scope="session")
def boto3_session(aws_credentials):
    # return boto3.session()
    with mock_aws():
        yield boto3.Session()
