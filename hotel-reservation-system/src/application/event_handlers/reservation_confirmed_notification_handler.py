"""予約確定 → 確認メール送信ハンドラ。"""

from __future__ import annotations

from src.domain.events.events import ReservationConfirmed
from src.domain.services.notification_service import NotificationService


class ReservationConfirmedNotificationHandler:
    def __init__(self, notification_service: NotificationService) -> None:
        self._notification_service = notification_service

    async def handle(self, event: ReservationConfirmed) -> None:
        await self._notification_service.send_reservation_confirmed(
            guest_id=event.guest_id,
            reservation_number=event.reservation_number,
            stay_period=event.stay_period,
            total_amount=event.total_amount,
        )
