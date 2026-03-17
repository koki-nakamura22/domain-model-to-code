"""予約変更 → 変更通知送信ハンドラ。"""

from __future__ import annotations

from src.domain.events.events import ReservationModified
from src.domain.services.notification_service import NotificationService


class ReservationModifiedNotificationHandler:
    def __init__(self, notification_service: NotificationService) -> None:
        self._notification_service = notification_service

    async def handle(self, event: ReservationModified) -> None:
        await self._notification_service.send_reservation_modified(
            guest_id=event.guest_id,
            reservation_number=event.reservation_number,
            new_stay_period=event.new_stay_period,
            new_total_amount=event.new_total_amount,
            amount_difference=event.amount_difference,
        )
