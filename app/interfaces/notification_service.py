from typing import Protocol

from app.models.notification import Notification


class NotificationService(Protocol):
    async def send_notification(self, notification: Notification) -> None:
        pass
