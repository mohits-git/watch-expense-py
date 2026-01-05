from aioboto3.session import Session
import aioboto3


def get_boto3_session() -> Session:
    session = aioboto3.Session()
    return session
