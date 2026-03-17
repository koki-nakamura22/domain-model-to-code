"""予約キャンセル → キャンセル通知送信ハンドラ。"""

from __future__ import annotations

from src.domain.events.events import ReservationCancelled
from src.domain.services.notification_service import NotificationService


class ReservationCancelledNotificationHandler:
    def __init__(self, notification_service: NotificationService) -> None:
        self._notification_service = notification_service

    async def handle(self, event: ReservationCancelled) -> None:
        await self._notification_service.send_reservation_cancelled(
            guest_id=event.guest_id,
            reservation_number=event.reservation_number,
            cancellation_fee=event.cancellation_fee,
            refund_amount=event.refund_amount,
        )
