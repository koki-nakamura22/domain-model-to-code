"""決済失敗 → 仮予約即時失効ハンドラ。"""

from __future__ import annotations

import datetime

from src.domain.events.events import PaymentFailed, ReservationExpired
from src.domain.repositories.reservation_repository import ReservationRepository
from src.domain.services.event_publisher import EventPublisher


class PaymentFailedHandler:
    def __init__(self, reservation_repo: ReservationRepository, event_publisher: EventPublisher) -> None:
        self._reservation_repo = reservation_repo
        self._event_publisher = event_publisher

    async def handle(self, event: PaymentFailed) -> None:
        reservation = await self._reservation_repo.find_by_id(event.reservation_id)
        if not reservation:
            return

        reservation.expire()
        await self._reservation_repo.save(reservation)

        await self._event_publisher.publish(
            ReservationExpired(
                occurred_at=datetime.datetime.now(tz=datetime.UTC),
                reservation_id=reservation.id,
                hotel_id=reservation.hotel_id,
                room_type_id=reservation.room_type_id,
                stay_period=reservation.stay_period,
            )
        )
