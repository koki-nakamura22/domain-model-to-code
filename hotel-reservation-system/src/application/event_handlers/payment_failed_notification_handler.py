"""決済失敗 → 決済失敗通知送信ハンドラ。"""

from __future__ import annotations

from src.domain.events.events import PaymentFailed
from src.domain.services.notification_service import NotificationService


class PaymentFailedNotificationHandler:
    def __init__(self, notification_service: NotificationService) -> None:
        self._notification_service = notification_service

    async def handle(self, event: PaymentFailed) -> None:
        await self._notification_service.send_payment_failed(
            reservation_id=event.reservation_id,
            reason=event.failure_reason,
        )
