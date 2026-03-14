"""仮予約失効ユースケース。"""

from __future__ import annotations

import datetime

from src.domain.events.events import ReservationExpired
from src.domain.repositories.reservation_repository import ReservationRepository
from src.domain.services.event_publisher import EventPublisher


class ExpireReservationsUseCase:
    def __init__(
        self,
        reservation_repo: ReservationRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._reservation_repo = reservation_repo
        self._event_publisher = event_publisher

    async def execute(self) -> int:
        now = datetime.datetime.now(tz=datetime.UTC)
        expired = await self._reservation_repo.find_expired_held(now)

        for reservation in expired:
            reservation.expire()
            await self._reservation_repo.save(reservation)
            await self._event_publisher.publish(
                ReservationExpired(
                    occurred_at=now,
                    reservation_id=reservation.id,
                    hotel_id=reservation.hotel_id,
                    room_type_id=reservation.room_type_id,
                    stay_period=reservation.stay_period,
                )
            )

        return len(expired)
