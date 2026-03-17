"""ノーショー検知 → ノーショー通知送信ハンドラ。"""

from __future__ import annotations

from src.domain.events.events import NoShowDetected
from src.domain.services.notification_service import NotificationService


class NoShowDetectedNotificationHandler:
    def __init__(self, notification_service: NotificationService) -> None:
        self._notification_service = notification_service

    async def handle(self, event: NoShowDetected) -> None:
        await self._notification_service.send_no_show_detected(
            guest_id=event.guest_id,
            reservation_number=event.reservation_number,
            total_amount=event.total_amount,
        )
