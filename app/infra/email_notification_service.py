from botocore.exceptions import ClientError
from app.errors.codes import AppErr
from app.models.notification import Notification
from mypy_boto3_sqs import SQSClient
from app.errors.app_exception import AppException


class EmailNotificationService:
    def __init__(self, client: SQSClient, email_queue_url: str):
        self._client = client
        self._email_queue_url = email_queue_url

    async def send_notification(self, notification: Notification) -> None:
        try:
            self._client.send_message(
                QueueUrl=self._email_queue_url,
                MessageBody=notification.model_dump_json(exclude_none=True),
            )
        except ClientError as e:
            raise AppException(AppErr.SQS_SEND_MESSAGE_FAILED, cause=e)
